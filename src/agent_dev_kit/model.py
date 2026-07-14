"""Versioned manifest model and path-safe asset resolution."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableSet, Optional, Sequence, Tuple

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


class ManifestError(ValueError):
    """Raised when the manifest or a referenced asset is invalid."""


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(path: Path) -> str:
    if path.is_symlink():
        return sha256_bytes(("symlink\0" + os.readlink(str(path))).encode("utf-8"))
    if path.is_file():
        return sha256_file(path)
    if not path.is_dir():
        raise ManifestError("asset path does not exist: {}".format(path))

    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file() or item.is_symlink()):
        relative = child.relative_to(path).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        if child.is_symlink():
            digest.update(("symlink\0" + os.readlink(str(child))).encode("utf-8"))
        else:
            digest.update(bytes.fromhex(sha256_file(child)))
    return digest.hexdigest()


def ensure_within(path: Path, root: Path, label: str = "path") -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ManifestError("{} escapes allowed root: {}".format(label, path)) from exc
    return resolved


@dataclass(frozen=True)
class Asset:
    kind: str
    name: str
    path: Path
    optional: bool = False

    @property
    def digest(self) -> str:
        return sha256_tree(self.path)


@dataclass(frozen=True)
class ProfileResolution:
    profiles: Tuple[str, ...]
    agents: Tuple[Asset, ...]
    skills: Tuple[Asset, ...]


class Manifest:
    ASSET_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
    REQUIRED_TOP_LEVEL = (
        "schema_version",
        "version",
        "product",
        "agents",
        "skills",
        "optional_skills",
        "profiles",
        "workflows",
        "tool_targets",
        "external_handoff_targets",
    )

    def __init__(self, root: Path, data: Mapping[str, Any], source: Path) -> None:
        self.root = root.resolve()
        self.data = dict(data)
        self.source = source.resolve()

    @classmethod
    def load(cls, root: Path, source: Optional[Path] = None) -> "Manifest":
        root = root.resolve()
        source = (source or root / "manifest.json").resolve()
        if not source.is_file():
            raise ManifestError("manifest not found: {}".format(source))
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ManifestError("invalid JSON manifest: {}".format(exc)) from exc
        if not isinstance(data, dict):
            raise ManifestError("manifest root must be an object")
        manifest = cls(root, data, source)
        failures = manifest._json_schema_failures()
        if failures:
            raise ManifestError("manifest schema validation failed: {}".format("; ".join(failures)))
        return manifest

    @property
    def version(self) -> str:
        return str(self.data.get("version", ""))

    @property
    def digest(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.data))

    @property
    def default_profile(self) -> str:
        return str(self.data.get("default_profile", "core"))

    def _records(self, key: str) -> List[Mapping[str, Any]]:
        value = self.data.get(key, [])
        if not isinstance(value, list):
            raise ManifestError("{} must be an array".format(key))
        records: List[Mapping[str, Any]] = []
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                raise ManifestError("{}[{}] must be an object".format(key, index))
            records.append(item)
        return records

    def _record_index(self, key: str) -> Dict[str, Mapping[str, Any]]:
        result: Dict[str, Mapping[str, Any]] = {}
        for item in self._records(key):
            name = str(item.get("name", ""))
            if not name:
                raise ManifestError("{} entry missing name".format(key))
            if name in result:
                raise ManifestError("duplicate {} entry: {}".format(key, name))
            result[name] = item
        return result

    def _manifest_schema(self) -> Mapping[str, Any]:
        candidates = (
            self.root / "manifests" / "manifest.schema.json",
            self.root / "source" / "manifests" / "manifest.schema.json",
        )
        path = next((item for item in candidates if item.is_file() and not item.is_symlink()), candidates[0])
        if path.is_symlink() or not path.is_file():
            raise ManifestError("manifest schema missing or unsafe: {}".format(path))
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ManifestError("manifest schema is invalid JSON: {}".format(path)) from exc
        if not isinstance(value, dict):
            raise ManifestError("manifest schema must be a JSON object")
        try:
            Draft202012Validator.check_schema(value)
        except SchemaError as exc:
            raise ManifestError("manifest schema is not valid Draft 2020-12: {}".format(exc.message)) from exc
        return value

    def _json_schema_failures(self) -> List[str]:
        try:
            schema = self._manifest_schema()
        except ManifestError as exc:
            return [str(exc)]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        failures: List[str] = []
        for error in sorted(
            validator.iter_errors(self.data),
            key=lambda item: tuple(str(part) for part in item.absolute_path),
        ):
            location = "/".join(str(item) for item in error.absolute_path) or "<root>"
            failures.append("schema {}: {}".format(location, error.message))
        return failures

    def validate(self, strict: bool = False) -> List[str]:
        failures: List[str] = self._json_schema_failures()
        for key in self.REQUIRED_TOP_LEVEL:
            if key not in self.data:
                failures.append("manifest missing top-level key: {}".format(key))

        try:
            expected_schema_version = self._manifest_schema()["properties"]["schema_version"]["const"]
        except (ManifestError, KeyError, TypeError):
            expected_schema_version = None
        if expected_schema_version and self.data.get("schema_version") != expected_schema_version:
            failures.append("schema_version must be {}".format(expected_schema_version))
        if not re.fullmatch(r"3\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", self.version):
            failures.append("version must be a semantic version with major 3")

        product = self.data.get("product")
        expected_product = {
            "kind": "agent-asset-platform",
            "runtime_boundary": "no-llm-runner",
            "evidence_model": "source-test-runtime-field",
        }
        if product != expected_product:
            failures.append("product contract does not match the v3 asset-platform boundary")

        try:
            agents = self._record_index("agents")
            skills = self._record_index("skills")
            optional = self._record_index("optional_skills")
        except ManifestError as exc:
            failures.append(str(exc))
            return failures

        overlap = set(skills).intersection(optional)
        if overlap:
            failures.append("optional skills duplicate core skills: {}".format(", ".join(sorted(overlap))))

        for key, records in (("agents", agents), ("skills", skills), ("optional_skills", optional)):
            for name, record in records.items():
                if not self.ASSET_NAME.fullmatch(name):
                    failures.append("{} entry has invalid name: {}".format(key, name))
                raw_path = record.get("path")
                if not isinstance(raw_path, str) or not raw_path:
                    failures.append("{} {} missing path".format(key, name))
                    continue
                candidate = self.root / raw_path
                try:
                    ensure_within(candidate, self.root, "asset path")
                except ManifestError as exc:
                    failures.append(str(exc))
                    continue
                if not candidate.is_file():
                    failures.append("{} {} path missing: {}".format(key, name, raw_path))

        profiles = self.data.get("profiles")
        if not isinstance(profiles, dict) or not profiles:
            failures.append("profiles must be a non-empty object")
        else:
            for profile, raw_profile in profiles.items():
                if not self.ASSET_NAME.fullmatch(str(profile)):
                    failures.append("profile has invalid name: {}".format(profile))
                    continue
                if not isinstance(raw_profile, dict):
                    failures.append("profile {} must be an object".format(profile))
                    continue
                parent = raw_profile.get("extends")
                if parent is not None and not isinstance(parent, str):
                    failures.append("profile {} extends must be a string".format(profile))
                for field in ("include_agents", "include_skills"):
                    values = raw_profile.get(field, [])
                    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                        failures.append("profile {} {} must be an array of strings".format(profile, field))
                        continue
                try:
                    self.resolve_profiles([profile])
                except ManifestError as exc:
                    failures.append(str(exc))

        if isinstance(profiles, dict) and self.default_profile not in profiles:
            failures.append("default_profile does not exist: {}".format(self.default_profile))

        direct = self.data.get("tool_targets")
        external = self.data.get("external_handoff_targets")
        if not isinstance(direct, dict) or not direct:
            failures.append("tool_targets must be a non-empty object")
        if not isinstance(external, dict):
            failures.append("external_handoff_targets must be an object")
        if isinstance(direct, dict) and isinstance(external, dict):
            duplicated_targets = set(direct).intersection(external)
            if duplicated_targets:
                failures.append("targets cannot be both direct and external: {}".format(", ".join(sorted(duplicated_targets))))
        if isinstance(direct, dict):
            for name, config in direct.items():
                if not self.ASSET_NAME.fullmatch(str(name)) or not isinstance(config, dict):
                    failures.append("invalid direct target: {}".format(name))
                    continue
                for field in ("agents_dir", "skills_dir"):
                    value = config.get(field)
                    if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts:
                        failures.append("target {} has unsafe {}".format(name, field))
                if self.data.get("schema_version") == "3.1.0":
                    supported = config.get("supported_asset_kinds")
                    if not isinstance(supported, list) or not supported or not all(
                        item in ("agent", "skill") for item in supported
                    ):
                        failures.append("target {} has invalid supported_asset_kinds".format(name))

        if strict:
            if self.data.get("schema_version") == "3.1.0":
                try:
                    from .targets import load_target_contract

                    for name, config in self.direct_targets().items():
                        contract = load_target_contract(self, name)
                        if list(contract.supported_asset_kinds) != config.get("supported_asset_kinds"):
                            failures.append(
                                "target {} manifest supported_asset_kinds differs from contract".format(name)
                            )
                        if contract.status != config.get("status"):
                            failures.append("target {} manifest status differs from contract".format(name))
                except ManifestError as exc:
                    failures.append(str(exc))
            workflows = {str(item.get("name", "")): item for item in self._records("workflows")}
            for name, workflow in workflows.items():
                if not self.ASSET_NAME.fullmatch(name):
                    failures.append("workflow entry has invalid name: {}".format(name or "<empty>"))
                    continue
                raw_path = workflow.get("path")
                if not isinstance(raw_path, str) or not raw_path:
                    failures.append("workflow {} path missing: {}".format(name, raw_path))
                    continue
                try:
                    workflow_path = ensure_within(self.root / raw_path, self.root, "workflow path")
                except ManifestError as exc:
                    failures.append(str(exc))
                    continue
                if not workflow_path.is_file():
                    failures.append("workflow {} path missing: {}".format(name, raw_path))

        return failures

    def _asset(self, kind: str, name: str, optional: bool = False) -> Asset:
        key = "optional_skills" if optional else ("agents" if kind == "agent" else "skills")
        record = self._record_index(key).get(name)
        if record is None:
            raise ManifestError("unknown {}: {}".format(key.rstrip("s"), name))
        path = self.root / str(record["path"])
        if kind == "agent":
            path = path.parent
        elif optional:
            path = path.parent
        else:
            path = path.parent
        ensure_within(path, self.root, "asset path")
        return Asset(kind=kind, name=name, path=path, optional=optional)

    def asset_record(self, asset: Asset) -> Mapping[str, Any]:
        key = "optional_skills" if asset.optional else ("agents" if asset.kind == "agent" else "skills")
        record = self._record_index(key).get(asset.name)
        if record is None:
            raise ManifestError("unknown {} asset record: {}".format(asset.kind, asset.name))
        return record

    def all_assets(self, kind: str) -> Tuple[Asset, ...]:
        if kind == "agent":
            return tuple(self._asset("agent", name) for name in self._record_index("agents"))
        if kind == "skill":
            core = [self._asset("skill", name) for name in self._record_index("skills")]
            optional = [self._asset("skill", name, optional=True) for name in self._record_index("optional_skills")]
            return tuple(core + optional)
        raise ManifestError("unknown asset kind: {}".format(kind))

    def resolve_profiles(
        self,
        profiles: Sequence[str],
        optional_skills: Sequence[str] = (),
    ) -> ProfileResolution:
        profile_map = self.data.get("profiles")
        if not isinstance(profile_map, dict):
            raise ManifestError("profiles must be an object")

        ordered_profiles: List[str] = []
        agent_names: List[str] = []
        skill_names: List[str] = []
        visiting: MutableSet[str] = set()
        visited: MutableSet[str] = set()

        def add_unique(target: List[str], values: Iterable[Any]) -> None:
            for value in values:
                name = str(value)
                if name not in target:
                    target.append(name)

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise ManifestError("profile inheritance cycle at {}".format(name))
            raw = profile_map.get(name)
            if not isinstance(raw, dict):
                raise ManifestError("unknown profile: {}".format(name))
            visiting.add(name)
            parent = raw.get("extends")
            if parent:
                visit(str(parent))
            visiting.remove(name)
            visited.add(name)
            ordered_profiles.append(name)
            add_unique(agent_names, raw.get("include_agents", []))
            add_unique(skill_names, raw.get("include_skills", []))

        for profile in profiles:
            visit(profile)

        agents = tuple(self._asset("agent", name) for name in agent_names)
        skills_list = [self._asset("skill", name) for name in skill_names]
        for name in optional_skills:
            if name in skill_names:
                raise ManifestError("optional skill duplicates resolved core skill: {}".format(name))
            skills_list.append(self._asset("skill", name, optional=True))
        return ProfileResolution(tuple(ordered_profiles), agents, tuple(skills_list))

    def direct_targets(self) -> Mapping[str, Mapping[str, Any]]:
        value = self.data.get("tool_targets", {})
        if not isinstance(value, dict):
            raise ManifestError("tool_targets must be an object")
        return value

    def external_targets(self) -> Mapping[str, Mapping[str, Any]]:
        value = self.data.get("external_handoff_targets", {})
        if not isinstance(value, dict):
            raise ManifestError("external_handoff_targets must be an object")
        return value

    def target(self, name: str) -> Mapping[str, Any]:
        target = self.direct_targets().get(name)
        if not isinstance(target, dict):
            if name in self.external_targets():
                raise ManifestError("target is external handoff only, not direct export: {}".format(name))
            raise ManifestError("unknown direct target: {}".format(name))
        return target
