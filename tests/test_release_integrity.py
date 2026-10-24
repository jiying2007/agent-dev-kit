"""Public release behavior binds Git inputs, archive contents and published assets."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from agent_dev_kit import release, target_contracts, targets
from agent_dev_kit.distribution import archive_io, release_artifacts, release_contract
from agent_dev_kit.model import Manifest, ManifestError, canonical_json_bytes
from release_archive_fixture import release_fixture

ROOT = Path(__file__).resolve().parents[1]


class ReleaseInventoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "agent-dev-kit-7.0.0.tar.gz"
        self.manifest, self.members = release_fixture()

    def write(self, members=None, special=None):
        values = list(self.members if members is None else members)
        values.append(("release-manifest.json", json.dumps(self.manifest).encode()))
        with tarfile.open(self.path, "w:gz") as archive:
            for name, payload in values:
                item = tarfile.TarInfo(name)
                item.size = len(payload)
                archive.addfile(item, io.BytesIO(payload))
            if special is not None:
                archive.addfile(special)
        self.path.with_name(self.path.name + ".sha256").write_text(
            hashlib.sha256(self.path.read_bytes()).hexdigest() + "  " + self.path.name + "\n")

    def update_source_inventory(self, members):
        source = {name[len("source/"):]: value for name, value in members if name.startswith("source/")}
        digest = hashlib.sha256()
        for name in sorted(source, key=Path):
            digest.update(name.encode() + b"\0" + hashlib.sha256(source[name]).digest())
        self.manifest["source_file_count"] = len(source)
        self.manifest["source_provenance"]["source_distribution_sha256"] = digest.hexdigest()

    def rewrite_source(self, replacements):
        members = dict(self.members)
        members.update(replacements)
        if "source/manifest.json" in replacements:
            members["manifest.json"] = replacements["source/manifest.json"]
            self.manifest["manifest_sha256"] = release_contract._canonical_manifest_sha256(members["manifest.json"])
        values = list(members.items())
        self.update_source_inventory(values)
        self.write(values)

    def amplified_frontmatter(self, rows, *, second_target=False):
        nested = {"rows": [0] * rows}
        for _ in range(50):
            nested = {"level": nested}
        changes = {}
        names = ["claude-code", "opencode"] if second_target else ["claude-code"]
        for target in names:
            path = "manifests/target-contracts/" + target + ".json"
            contract = json.loads((ROOT / path).read_bytes())
            for kind in ("agent", "skill"):
                contract["frontmatter"][kind]["static"]["amplification"] = nested
            changes["source/" + path] = json.dumps(contract, separators=(",", ":")).encode()
        if second_target:
            source = json.loads(dict(self.members)["source/manifest.json"])
            source["tool_targets"]["opencode"] = Manifest.load(ROOT).data["tool_targets"]["opencode"]
            changes["source/manifest.json"] = json.dumps(source).encode()
            self.manifest["direct_targets"].append({"target": "opencode", "agents": 1, "skills": 1})
        self.rewrite_source(changes)

    def aliased_skills(self, count, *, support=b"", empty_support_files=0):
        source = json.loads(dict(self.members)["source/manifest.json"])
        original = source["skills"][0]
        source["skills"] = [dict(original, name="budget-skill-" + str(index)) for index in range(count)]
        source["profiles"]["embedded-fullstack"]["include_skills"] = [item["name"] for item in source["skills"]]
        changes = {"source/manifest.json": json.dumps(source).encode(),
                   "source/" + original["path"]: b"---\ndescription: bounded alias fixture\n---\nbody\n"}
        if support:
            changes["source/" + str(Path(original["path"]).parent / "assets/payload.bin")] = support
        for index in range(empty_support_files):
            path = Path(original["path"]).parent / ("assets/empty-" + str(index) + ".txt")
            changes["source/" + str(path)] = b""
        self.manifest["direct_targets"][0]["skills"] = count
        self.rewrite_source(changes)

    def native_receipt_source(self, schema, *, registered=False):
        path = "source/manifests/target-contracts/claude-code.json"
        contract = json.loads(dict(self.members)[path])
        receipt = b"{}\n"
        contract["adapter"]["conformance"] = {
            "level": "runtime", "certification": "conformance-certified", "native_runtime_smoke": "pass",
            "runtime_binary": "offline-fixture", "runtime_binary_sha256": "a" * 64,
            "runtime_version": "offline-fixture-1", "runtime_version_pin": "offline-fixture-1",
            "last_verified_at": "2026-10-24T00:00:00Z",
            "evidence": [{"receipt_schema": "adk-native-target-conformance-receipt/v2",
                          "path": "reports/offline-fixture.json", "sha256": hashlib.sha256(receipt).hexdigest(),
                          "target": "claude-code", "runtime_version": "offline-fixture-1",
                          "bundle_sha256": "b" * 64, "contract_sha256": "c" * 64, "layer": "runtime"}],
        }
        contract["adapter"]["conformance_trust_policy"] = {
            "enabled": True, "trusted_authorities": ["offline-fixture"],
            "verification_backend": "external-signature-verifier",
        }
        for stage in ("discovery", "load", "trigger"):
            contract["adapter"]["capabilities"][stage] = "native-verified"
        registry = {"schema": "adk-native-conformance-trust-registry/v1", "status": "active",
                    "authority_model": "owner-reviewed-managed-registry", "authorities": {}}
        changes = {}
        if registered:
            contract["adapter"]["conformance_trust_policy"]["verification_backend"] = "ci-provenance-verifier"
            contract_digest = target_contracts._native_contract_digest(contract)
            now = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=1)
            stages = []
            for index, stage in enumerate(("discovery", "load", "trigger")):
                started = now - timedelta(minutes=4 - index)
                authority = {"execution_authority": "ci-approved", "authority_id": "offline-fixture", "scope": stage}
                authority["attestation_sha256"] = target_contracts._authority_digest(authority)
                stages.append({
                    "stage": stage, "command_sha256": str(index + 1) * 64,
                    "assertion_sha256": ("a", "b", "c")[index] * 64,
                    "assertion_result_sha256": ("d", "e", "f")[index] * 64,
                    "semantic_assertion_status": "pass", "result_sha256": str(index + 4) * 64,
                    "exit_code": 0, "started_at": started.isoformat(),
                    "completed_at": (started + timedelta(seconds=10)).isoformat(), "duration_ms": 10000,
                    "environment": {"platform": "linux", "architecture": "x86_64",
                                    "cwd_sha256": "7" * 64, "environment_sha256": "8" * 64,
                                    "runtime_binary_sha256": "a" * 64, "bundle_sha256": "b" * 64,
                                    "contract_sha256": contract_digest},
                    "privacy": {"raw_content_stored": False, "secrets_stored": False, "sanitized": True},
                    "authority": authority,
                })
            receipt_data = {
                "schema": "adk-native-target-conformance-receipt/v2", "receipt_id": "offline-fixture-native",
                "target": "claude-code", "runtime": {"binary": "offline-fixture", "binary_sha256": "a" * 64,
                                                     "version": "offline-fixture-1", "version_pin": "offline-fixture-1"},
                "bundle_sha256": "b" * 64, "contract_sha256": contract_digest,
                "verified_at": now.isoformat(), "stages": stages,
            }
            receipt = json.dumps(receipt_data).encode()
            conformance = contract["adapter"]["conformance"]
            conformance["last_verified_at"] = receipt_data["verified_at"]
            conformance["evidence"][0]["sha256"] = hashlib.sha256(receipt).hexdigest()
            conformance["evidence"][0]["contract_sha256"] = contract_digest
            binary = Path(sys.executable).resolve()
            signature = b'{"fixture":"not-a-real-signature"}\n'
            registry["authorities"]["offline-fixture"] = {
                "enabled": True, "policy_backend": "ci-provenance-verifier", "verifier": "sigstore-cosign-blob",
                "allowed_targets": ["claude-code"], "certificate_identity": "https://invalid.example/fixture",
                "certificate_oidc_issuer": "https://invalid.example/issuer",
                "cosign_binary": str(binary), "cosign_binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                "receipts": {receipt_data["receipt_id"]: {
                    "receipt_canonical_sha256": hashlib.sha256(canonical_json_bytes(receipt_data)).hexdigest(),
                    "bundle_path": "reports/offline-fixture.sigstore.json", "bundle_sha256": hashlib.sha256(signature).hexdigest(),
                }},
            }
            changes["source/reports/offline-fixture.sigstore.json"] = signature
        changes.update({
            path: json.dumps(contract).encode(),
            "source/manifests/native_conformance_trust_registry.json": json.dumps(registry).encode(),
            "source/reports/offline-fixture.json": receipt,
            "source/schemas/native-target-conformance-receipt-v2.schema.json": json.dumps(schema).encode(),
        })
        self.rewrite_source(changes)

    def test_real_source_inventory_is_accepted_in_any_member_order(self):
        self.write(list(reversed(self.members)))
        self.assertEqual("pass", release_contract.validate_release_artifact(self.path)["status"])

    def test_frontmatter_output_is_bounded_during_encoding(self):
        self.amplified_frontmatter(3000)
        with mock.patch.object(archive_io, "MAX_MEMBER_BYTES", 128 * 1024), \
             self.assertRaisesRegex(ValueError, "render_output_budget_exceeded.*file byte"):
            release_contract.validate_release_artifact(self.path)

    def test_cumulative_render_budget_is_shared_by_assets_and_targets(self):
        for second_target in (False, True):
            self.amplified_frontmatter(1500 if second_target else 3000, second_target=second_target)
            with self.subTest(second_target=second_target), \
                 mock.patch.object(archive_io, "MAX_DECODED_BYTES", 512 * 1024), \
                 mock.patch.object(archive_io, "MAX_MEMBER_BYTES", 384 * 1024), \
                 self.assertRaisesRegex(ValueError, "render_output_budget_exceeded.*total byte"):
                release_contract.validate_release_artifact(self.path)

    def test_aliased_source_assets_cannot_exceed_rendered_file_budget(self):
        self.aliased_skills(80)
        with mock.patch.object(archive_io, "MAX_MEMBERS", 64), \
             mock.patch.object(targets, "_render_main", wraps=targets._render_main) as render, \
             self.assertRaisesRegex(ValueError, "render_output_budget_exceeded.*file count"):
            release_contract.validate_release_artifact(self.path)
        self.assertLessEqual(render.call_count, 64)

    def test_repeated_support_output_uses_the_same_byte_budget(self):
        self.aliased_skills(20, support=b"x" * (48 * 1024))
        with mock.patch.object(archive_io, "MAX_DECODED_BYTES", 512 * 1024), \
             self.assertRaisesRegex(ValueError, "render_output_budget_exceeded.*total byte"):
            release_contract.validate_release_artifact(self.path)

    def test_export_manifest_itself_must_fit_the_rendered_file_budget(self):
        self.aliased_skills(10, empty_support_files=100)
        with mock.patch.object(archive_io, "MAX_MEMBER_BYTES", 128 * 1024), \
             self.assertRaisesRegex(ValueError, "render_output_budget_exceeded.*file byte"):
            release_contract.validate_release_artifact(self.path)

    def test_exact_output_limits_preserve_renderer_bytes(self):
        source = Path(self.temp.name) / "exact-source"
        for name, content in self.members:
            if name.startswith("source/"):
                path = source / name[len("source/"):]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        manifest = Manifest.load(source)
        expected = targets._render_historical_selection(manifest, "claude-code", ["embedded-fullstack"], (), None)
        limits = {"max_bytes": sum(len(item.content) for item in expected.files),
                  "max_file_bytes": max(len(item.content) for item in expected.files),
                  "max_files": len(expected.files),
                  "max_name_bytes": max(len(item.destination.encode()) for item in expected.files)}
        actual = targets._render_historical_selection(
            manifest, "claude-code", ["embedded-fullstack"], (), None, budget=targets.RenderBudget(**limits))
        self.assertEqual(expected.files, actual.files)
        for key, message in (("max_bytes", "total byte"), ("max_file_bytes", "file byte"),
                             ("max_files", "file count"), ("max_name_bytes", "file name")):
            lowered = dict(limits)
            lowered[key] -= 1
            with self.subTest(limit=key), self.assertRaisesRegex(ManifestError, "render_output_budget_exceeded.*" + message):
                targets._render_historical_selection(
                    manifest, "claude-code", ["embedded-fullstack"], (), None, budget=targets.RenderBudget(**lowered))

    def test_source_payload_drift_rejected_after_outer_checksum_is_recomputed(self):
        self.write([(name, b"changed\n" if name == "source/README.md" else raw)
                    for name, raw in self.members])
        with self.assertRaisesRegex(ValueError, "source distribution digest"):
            release_contract.validate_release_artifact(self.path)

    def test_missing_extra_and_false_source_count_are_rejected(self):
        for members in ([item for item in self.members if item[0] != "source/README.md"],
                        self.members + [("source/extra.txt", b"extra")]):
            self.write(members)
            with self.subTest(members=len(members)), self.assertRaisesRegex(ValueError, "source file count"):
                release_contract.validate_release_artifact(self.path)
        self.manifest["source_file_count"] += 1
        self.write()
        with self.assertRaisesRegex(ValueError, "source file count"):
            release_contract.validate_release_artifact(self.path)

    def test_embedded_source_manifest_must_match_top_level(self):
        self.write([(name, b'{"version":"7.0.1"}' if name == "source/manifest.json" else raw)
                    for name, raw in self.members])
        with self.assertRaisesRegex(ValueError, "source manifest"):
            release_contract.validate_release_artifact(self.path)

    def test_archived_python_is_data_and_never_imported(self):
        members = self.members + [("source/src/agent_dev_kit/compiler.py",
                                   b'raise RuntimeError("archive Python was executed")\n')]
        self.update_source_inventory(members)
        self.write(members)
        self.assertEqual("pass", release_contract.validate_release_artifact(self.path)["status"])

    def test_source_schema_cannot_request_external_references(self):
        for schema in ("manifest.schema.json", "target-contract.schema.json"):
            for value in ({"$ref": "https://invalid.example/never-fetch.json"},
                          {"$recursiveRef": "https://invalid.example/never-fetch.json"},
                          {"$defs": {"nested": {"$id": "https://invalid.example/scope"}}},
                          {"$defs": {"nested": {"id": "https://invalid.example/legacy-scope"}}}):
                name = "source/manifests/" + schema
                members = [(path, json.dumps(value).encode() if path == name else raw)
                           for path, raw in self.members]
                self.update_source_inventory(members)
                self.write(members)
                with self.subTest(schema=schema, value=value), self.assertRaisesRegex(ValueError, "bundle source schema"):
                    release_contract.validate_release_artifact(self.path)

    def test_native_receipt_schema_is_checked_before_reference_resolution(self):
        for reference in ("$ref", "$dynamicRef"):
            self.native_receipt_source({reference: "https://invalid.example/never-request.json"})
            with self.subTest(reference=reference), \
                 mock.patch("urllib.request.urlopen", side_effect=AssertionError("external I/O forbidden")) as network:
                with self.assertRaises(ValueError) as caught:
                    release_contract.validate_release_artifact(self.path)
                network.assert_not_called()
                self.assertIn("bundle source schema must use local references", str(caught.exception))

    def test_local_native_schema_preserves_receipt_validation(self):
        schema = json.loads((ROOT / "schemas/native-target-conformance-receipt-v2.schema.json").read_bytes())
        self.native_receipt_source(schema)
        source = Path(self.temp.name) / "local-native-source"
        archive_io.inspect_archive_snapshot(self.path.read_bytes(), source_directory=source)
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("external I/O forbidden")) as network, \
             mock.patch("agent_dev_kit.native_trust.verify_sigstore_blob",
                        side_effect=AssertionError("invalid receipt must not reach verification")) as verifier:
            for loader in (target_contracts.load_target_contract, target_contracts._load_historical_target_contract):
                with self.subTest(loader=loader.__name__), \
                     self.assertRaisesRegex(ManifestError, "native receipt schema failure"):
                    loader(Manifest.load(source), "claude-code")
            network.assert_not_called()
            verifier.assert_not_called()

    def test_archive_registry_cannot_authorize_host_native_verifier_execution(self):
        schema = json.loads((ROOT / "schemas/native-target-conformance-receipt-v2.schema.json").read_bytes())
        self.native_receipt_source(schema, registered=True)
        with mock.patch("agent_dev_kit.sigstore_blob.subprocess.run",
                        side_effect=AssertionError("archive-selected execution blocked")) as process, \
             mock.patch.object(target_contracts, "build_managed_native_trust_verifier",
                               wraps=target_contracts.build_managed_native_trust_verifier) as verifier:
            with self.assertRaises(ValueError) as caught:
                release_contract.validate_release_artifact(self.path)
            process.assert_not_called()
            verifier.assert_not_called()
            self.assertIn("independently trusted verifier authority", str(caught.exception))

    def test_external_support_root_is_rejected_before_filesystem_inspection(self):
        outside = Path(self.temp.name) / "outside-source"
        outside.mkdir()
        (outside / "sentinel.txt").write_text("test-owned harmless content\n")
        contract_path = "source/manifests/target-contracts/claude-code.json"
        schema_path = "source/manifests/target-contract.schema.json"
        contract = json.loads(dict(self.members)[contract_path])
        contract["support_directories"] = [str(outside)]
        schema = json.loads(dict(self.members)[schema_path])
        schema["properties"]["support_directories"]["items"] = {"type": "string"}
        self.rewrite_source({contract_path: json.dumps(contract).encode(), schema_path: json.dumps(schema).encode()})
        inspected = []
        original_exists, original_rglob = Path.exists, Path.rglob

        def exists(path):
            if path == outside:
                inspected.append("exists")
            return original_exists(path)

        def rglob(path, pattern):
            if path == outside:
                inspected.append("rglob")
            return original_rglob(path, pattern)

        with mock.patch.object(Path, "exists", exists), mock.patch.object(Path, "rglob", rglob):
            with self.assertRaisesRegex(ManifestError, "asset support.*escapes allowed root"):
                release_contract.validate_release_artifact(self.path)
        self.assertEqual([], inspected)

    def test_malformed_local_schema_is_a_structured_contract_failure(self):
        for value in ({"$ref": "#"}, {"$ref": "#/$defs/missing"}):
            members = [(name, json.dumps(value).encode() if name == "source/manifests/manifest.schema.json" else raw)
                       for name, raw in self.members]
            self.update_source_inventory(members)
            self.write(members)
            output = io.StringIO()
            with self.subTest(schema=value), redirect_stdout(output):
                self.assertEqual(1, release_contract._main([str(self.path)]))
                result = json.loads(output.getvalue())
                self.assertEqual("fail", result["status"])
                self.assertIn("bundle", result["error"])

    def test_historical_bundle_remains_verifiable_after_source_expiry(self):
        self.write()
        contract = json.loads(dict(self.members)["source/manifests/target-contracts/claude-code.json"])
        expired = date.fromisoformat(contract["source"]["expires_at"]) + timedelta(days=1)
        with mock.patch.object(target_contracts, "date", wraps=date) as clock:
            clock.today.return_value = expired
            self.assertEqual("pass", release_contract.validate_release_artifact(self.path)["status"])
            with self.assertRaisesRegex(ManifestError, "target_contract_stale"):
                target_contracts.load_target_contract(Manifest.load(ROOT), "claude-code")

    def test_renamed_public_publish_is_rejected_before_github_discovery(self):
        self.write()
        renamed = self.path.with_name("agent-dev-kit-9.9.9.tar.gz")
        self.path.rename(renamed)
        renamed.with_name(renamed.name + ".sha256").write_text(
            hashlib.sha256(renamed.read_bytes()).hexdigest() + "  " + renamed.name + "\n")
        with mock.patch.object(release.shutil, "which", side_effect=AssertionError("premature gh discovery")):
            with self.assertRaisesRegex(ManifestError, "filename.*version"):
                release.publish_release("9.9.9", "github", renamed, dry_run=True)

    def test_all_duplicate_unsafe_and_special_members_are_rejected(self):
        for extra in (("source/README.md", b"duplicate"), ("source/../escape", b"bad"),
                      ("source//alias.txt", b"bad"), ("/absolute", b"bad"),
                      ("source", b"file hiding a directory")):
            self.write(self.members + [extra])
            with self.subTest(name=extra[0]), self.assertRaises(ValueError):
                release_contract.validate_release_artifact(self.path)
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE):
            item = tarfile.TarInfo("source/special")
            item.type = kind
            item.linkname = "README.md"
            self.write(special=item)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                release_contract.validate_release_artifact(self.path)


class ReleaseGitInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.template = cls.work / "template"
        release_artifacts._copy_source_distribution(Manifest.load(ROOT), cls.template)
        (cls.template / ".gitignore").write_text("docs/.cache/\n")
        cls.git(cls.template, "init", "-q")
        cls.git(cls.template, "add", "--all")
        cls.git(cls.template, "-c", "user.name=Release Fixture", "-c", "user.email=fixture@adk.invalid",
                "-c", "commit.gpgsign=false", "commit", "-qm", "frozen release inputs")
        cls.baseline = release.build_release(Manifest.load(cls.template), cls.work / "baseline")
        cls.baseline_bytes = Path(cls.baseline["artifact"]).read_bytes()

    @staticmethod
    def git(root, *arguments):
        return subprocess.run(["git", "-C", str(root), *arguments], check=True, capture_output=True,
                              env=dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull),
                              text=True, timeout=60).stdout.strip()

    def setUp(self):
        self.case = tempfile.TemporaryDirectory(dir=self.work)
        self.addCleanup(self.case.cleanup)
        self.root = Path(self.case.name)
        self.source = self.root / "source"
        self.git(self.work, "clone", "-q", "--no-hardlinks", str(self.template), str(self.source))

    def build(self):
        return release.build_release(Manifest.load(self.source), self.root / "dist")

    def bundle_variant(self, mutation):
        artifact = self.root / mutation / Path(self.baseline["artifact"]).name
        artifact.parent.mkdir()
        with tarfile.open(fileobj=io.BytesIO(self.baseline_bytes), mode="r:gz") as archive:
            members = [(copy.copy(item), archive.extractfile(item).read() if item.isfile() else None)
                       for item in archive]
        skill = next(item.name for item, _ in members
                     if item.isfile() and item.name.startswith("bundles/claude-code/")
                     and item.name.endswith("/SKILL.md"))
        replacement = b"# modified compiled skill\n"
        with tarfile.open(artifact, "w:gz") as archive:
            for item, payload in members:
                if mutation == "missing-all" and (item.name == "bundles" or item.name.startswith("bundles/")):
                    continue
                if mutation == "missing-target" and item.name.startswith("bundles/claude-code"):
                    continue
                if mutation == "missing-file" and item.name == skill:
                    continue
                if mutation == "missing-export-manifest" and item.name == "bundles/claude-code/adk-export-manifest.json":
                    continue
                if mutation == "changed-directory-mode" and item.name == "bundles/claude-code":
                    item.mode = 0o777
                if item.name == skill:
                    if mutation in ("changed-file", "self-rehashed-export-manifest"):
                        payload = replacement
                    if mutation == "changed-mode":
                        item.mode = 0o755 if item.mode == 0o644 else 0o644
                if mutation == "self-rehashed-export-manifest" and item.name == "bundles/claude-code/adk-export-manifest.json":
                    inventory = json.loads(payload)
                    for record in inventory["files"]:
                        if "bundles/claude-code/" + record["path"] == skill:
                            record["sha256"] = hashlib.sha256(replacement).hexdigest()
                    payload = json.dumps(inventory, ensure_ascii=False, indent=2).encode() + b"\n"
                if mutation == "false-target-count" and item.name == "release-manifest.json":
                    manifest = json.loads(payload)
                    manifest["direct_targets"][0]["skills"] += 1
                    payload = json.dumps(manifest).encode()
                if payload is not None:
                    item.size = len(payload)
                archive.addfile(item, io.BytesIO(payload) if payload is not None else None)
            if mutation == "extra-file":
                item = tarfile.TarInfo("bundles/claude-code/unmanaged.txt")
                item.size = len(replacement)
                item.mode = 0o644
                archive.addfile(item, io.BytesIO(replacement))
            if mutation == "extra-directory":
                item = tarfile.TarInfo("bundles/claude-code/unmanaged")
                item.type = tarfile.DIRTYPE
                item.mode = 0o755
                archive.addfile(item)
        artifact.with_name(artifact.name + ".sha256").write_text(
            hashlib.sha256(artifact.read_bytes()).hexdigest() + "  " + artifact.name + "\n")
        return artifact

    def test_real_bundle_bytes_modes_inventory_and_target_counts_are_required(self):
        for mutation in ("missing-all", "missing-target", "missing-file", "changed-file",
                         "extra-file", "changed-mode", "false-target-count", "missing-export-manifest",
                         "extra-directory", "changed-directory-mode"):
            artifact = self.bundle_variant(mutation)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "bundle"):
                release_contract.validate_release_artifact(artifact)

    def test_recomputed_export_manifest_cannot_authorize_a_changed_bundle(self):
        artifact = self.bundle_variant("self-rehashed-export-manifest")
        with self.assertRaisesRegex(ValueError, "bundle"):
            release_contract.validate_release_artifact(artifact)

    def test_public_publish_rejects_missing_bundles_before_github_discovery(self):
        artifact = self.bundle_variant("missing-all")
        with mock.patch.object(release.shutil, "which", side_effect=AssertionError("premature gh discovery")):
            with self.assertRaisesRegex(ManifestError, "bundle"):
                release.publish_release(self.baseline["version"], "github", artifact, dry_run=True)

    def test_real_clean_bundle_validation_remains_positive(self):
        artifact = self.root / Path(self.baseline["artifact"]).name
        artifact.write_bytes(self.baseline_bytes)
        self.assertEqual("pass", release_contract.validate_release_artifact(artifact)["status"])

    def test_ignored_file_cannot_enter_clean_commit_release(self):
        ignored = self.source / "docs/.cache/review-sentinel.txt"
        ignored.parent.mkdir()
        ignored.write_text("ignored residue\n")
        self.assertEqual("", self.git(self.source, "status", "--porcelain", "--untracked-files=all"))
        result = self.build()
        self.assertTrue(result["release_eligible"])
        self.assertEqual(self.baseline["source_file_count"], result["source_file_count"])
        self.assertEqual(self.baseline_bytes, Path(result["artifact"]).read_bytes())

    def test_hidden_tracked_drift_cannot_change_frozen_release(self):
        for flag in ("--assume-unchanged", "--skip-worktree"):
            self.git(self.source, "update-index", "--no-assume-unchanged", "README.md")
            self.git(self.source, "update-index", flag, "README.md")
            (self.source / "README.md").write_text("hidden worktree drift\n")
            self.assertEqual("", self.git(self.source, "status", "--porcelain", "--untracked-files=all"))
            result = self.build()
            with self.subTest(flag=flag):
                self.assertEqual(self.baseline_bytes, Path(result["artifact"]).read_bytes())

    def test_git_export_attributes_do_not_substitute_or_omit_tracked_blobs(self):
        (self.source / ".gitattributes").write_text("README.md export-ignore\ndocs/identity.txt export-subst\n")
        (self.source / "docs/identity.txt").write_text("$Format:%H$\n")
        self.git(self.source, "add", ".gitattributes", "docs/identity.txt")
        self.git(self.source, "-c", "user.name=Release Fixture", "-c", "user.email=fixture@adk.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "attributes are not release authority")
        result = self.build()
        with tarfile.open(result["artifact"], "r:gz") as archive:
            self.assertIsNotNone(archive.getmember("source/README.md"))
            self.assertEqual(b"$Format:%H$\n", archive.extractfile("source/docs/identity.txt").read())

    def test_local_replacement_ref_cannot_redefine_a_frozen_blob(self):
        original = self.git(self.source, "rev-parse", "HEAD:README.md")
        replacement = self.root / "replacement.txt"
        replacement.write_text("local replacement is not a commit blob\n")
        substituted = self.git(self.source, "hash-object", "-w", str(replacement))
        self.git(self.source, "replace", original, substituted)
        result = self.build()
        self.assertEqual(self.baseline_bytes, Path(result["artifact"]).read_bytes())

    def test_dirty_developer_build_remains_explicitly_ineligible(self):
        with (self.source / "README.md").open("a") as stream:
            stream.write("developer edit\n")
        with self.assertRaisesRegex(ManifestError, "clean source"):
            self.build()
        result = release.build_release(Manifest.load(self.source), self.root / "developer",
                                       allow_unbound_snapshot=True)
        self.assertFalse(result["release_eligible"])
        self.assertEqual("git-working-tree-snapshot", result["source_provenance"]["kind"])
        self.assertFalse(release_contract.validate_release_artifact(Path(result["artifact"]))["release_eligible"])

    @unittest.skipUnless(os.name == "posix", "POSIX symlink")
    def test_tracked_symlink_rejected_without_copying_its_target(self):
        (self.source / "docs/linked").symlink_to("../README.md")
        self.git(self.source, "add", "docs/linked")
        self.git(self.source, "-c", "user.name=Release Fixture", "-c", "user.email=fixture@adk.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "unsupported tracked type")
        with self.assertRaisesRegex(ManifestError, "unsupported.*type|symlinks"):
            self.build()

    def test_public_publish_plans_and_uploads_the_complete_verified_snapshot(self):
        artifact = self.root / Path(self.baseline["artifact"]).name
        artifact.write_bytes(self.baseline_bytes)
        checksum = artifact.with_name(artifact.name + ".sha256")
        checksum.write_text(hashlib.sha256(self.baseline_bytes).hexdigest() + "  " + artifact.name + "\n")
        version = self.baseline["version"]
        with mock.patch.object(release.shutil, "which", return_value="/fixture/gh"):
            plan = release.publish_release(version, "github", artifact, dry_run=True)
        self.assertEqual([artifact.name, checksum.name, "release-contract.json"],
                         [Path(value).name for value in plan["command"][4:7]])
        self.assertFalse((self.root / "release-contract.json").exists())
        capture = release_artifacts._verified_archive_snapshot
        observed = []

        def captured(path):
            value = capture(path)
            path.write_bytes(b"REPLACED AFTER VERIFICATION")
            return value

        def uploaded(command, **_kwargs):
            archive, sidecar, contract = map(Path, command[4:7])
            self.assertEqual(self.baseline_bytes, archive.read_bytes())
            self.assertEqual(hashlib.sha256(self.baseline_bytes).hexdigest(), sidecar.read_text().split()[0])
            data = json.loads(contract.read_text())
            self.assertEqual("adk-release-artifact-contract-set/v1", data["schema"])
            self.assertEqual(hashlib.sha256(self.baseline_bytes).hexdigest(), data["artifacts"][0]["artifact_sha256"])
            self.assertTrue(data["artifacts"][0]["release_eligible"])
            observed.append(archive)
            return mock.Mock(returncode=0, stdout="fixture publication", stderr="")

        with mock.patch.object(release_artifacts, "_verified_archive_snapshot", side_effect=captured), \
             mock.patch.object(release.shutil, "which", return_value="/fixture/gh"), \
             mock.patch.object(release.subprocess, "run", side_effect=uploaded):
            self.assertEqual("pass", release.publish_release(version, "github", artifact)["status"])
        self.assertEqual(1, len(observed))
        self.assertFalse(observed[0].exists())


if __name__ == "__main__":
    unittest.main()
