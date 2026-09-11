"""Portable, content-addressed promotion evidence for cross-repository consumers.

The evidence file is intentionally self-contained and can be copied into a
consumer repository. GitHub Actions signs this file with a keyless Sigstore
attestation; consumers verify the detached bundle without checking out this
private repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from agent_dev_kit.contracts.schema_loader import packaged_schema_bytes
from agent_dev_kit.model import canonical_json_bytes

_SCHEMA_NAME = "promotion-evidence-v1.schema.json"
_REQUIRED_PYTHON = ["3.11", "3.12"]


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def _schema_set_sha256(root: Path) -> str:
    entries = []
    for path in sorted((root / "schemas").glob("*.schema.json")):
        entries.append({"path": path.relative_to(root).as_posix(), "sha256": _sha256_file(path)})
    if not entries:
        raise ValueError("schema set is empty")
    return _sha256(canonical_json_bytes(entries))


def _load_release_contract(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping) or value.get("schema") != "adk-release-artifact-contract-set/v1":
        raise ValueError("release contract must be adk-release-artifact-contract-set/v1")
    artifacts = value.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 1 or not isinstance(artifacts[0], Mapping):
        raise ValueError("release contract must contain exactly one artifact")
    artifact = artifacts[0]
    if artifact.get("status") not in (None, "pass"):
        raise ValueError("release contract artifact is not passing")
    return artifact


def validate_promotion_evidence(value: Mapping[str, Any]) -> dict[str, Any]:
    schema = json.loads(packaged_schema_bytes(_SCHEMA_NAME).decode("utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures = sorted(error.message for error in validator.iter_errors(dict(value)))

    source = value.get("source")
    ci = value.get("ci")
    if isinstance(source, Mapping):
        if source.get("repository") != "jiying2007/agent-dev-kit":
            failures.append("source.repository must be jiying2007/agent-dev-kit")
        if source.get("ref") != "refs/heads/main":
            failures.append("source.ref must be refs/heads/main")
        if source.get("event") != "push":
            failures.append("source.event must be push")
    if isinstance(ci, Mapping):
        for key in ("contract_matrix", "regression_matrix"):
            matrix = ci.get(key)
            if isinstance(matrix, Mapping) and matrix.get("python") != _REQUIRED_PYTHON:
                failures.append(f"ci.{key}.python must be {_REQUIRED_PYTHON}")

    return {
        "schema": "adk-promotion-evidence-validation/v1",
        "status": "pass" if not failures else "fail",
        "failures": sorted(set(failures)),
    }


def build_promotion_evidence(
    *,
    root: Path,
    release_contract_path: Path,
    repository: str,
    ref: str,
    event: str,
    workflow: str,
    workflow_ref: str,
    workflow_sha: str,
    run_id: int,
    run_attempt: int,
    contract_result: str,
    regression_result: str,
    static_security_result: str,
    deterministic_result: str,
) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest.json root must be an object")

    release = _load_release_contract(release_contract_path)
    version = str(manifest.get("version", ""))
    if not version or release.get("version") != version:
        raise ValueError("release contract version must match manifest version")

    required_results = {
        "contract": contract_result,
        "regression": regression_result,
        "static-security": static_security_result,
        "deterministic-eval-package": deterministic_result,
    }
    failed = sorted(name for name, result in required_results.items() if result != "success")
    if failed:
        raise ValueError("promotion evidence requires successful CI claims: " + ", ".join(failed))

    commit = _git("rev-parse", "HEAD", cwd=root)
    tree = _git("rev-parse", "HEAD^{tree}", cwd=root)
    manifest_blob = _git("hash-object", "manifest.json", cwd=root)
    manifest_sha256 = _sha256(canonical_json_bytes(dict(manifest)))

    evidence: dict[str, Any] = {
        "schema": "adk-promotion-evidence/v1",
        "issued_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source": {
            "repository": repository,
            "version": version,
            "commit": commit,
            "tree": tree,
            "manifest_blob": manifest_blob,
            "manifest_sha256": manifest_sha256,
            "ref": ref,
            "event": event,
            "workflow": workflow,
            "workflow_ref": workflow_ref,
            "workflow_sha": workflow_sha,
            "run_id": run_id,
            "run_attempt": run_attempt,
        },
        "contracts": {
            "contract_registry_sha256": _sha256_file(root / "manifests" / "contract_registry.json"),
            "schema_set_sha256": _schema_set_sha256(root),
            "release_manifest_sha256": str(release["release_manifest_sha256"]),
        },
        "ci": {
            "contract_matrix": {"status": "success", "python": _REQUIRED_PYTHON},
            "regression_matrix": {"status": "success", "python": _REQUIRED_PYTHON},
            "static_security": "success",
            "deterministic_eval_package": "success",
        },
        "release": {
            "artifact_sha256": str(release["artifact_sha256"]),
            "release_eligible": bool(release["release_eligible"]),
        },
        "provenance": {
            "subject": "promotion-evidence.json",
            "format": "sigstore-bundle/v1",
        },
    }
    validation = validate_promotion_evidence(evidence)
    if validation["status"] != "pass":
        raise ValueError("promotion evidence validation failed: " + "; ".join(validation["failures"]))
    return evidence


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or validate portable ADK promotion evidence")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate")
    generate.add_argument("--root", type=Path, default=Path.cwd())
    generate.add_argument("--release-contract", type=Path, required=True)
    generate.add_argument("--out", type=Path, required=True)
    generate.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    generate.add_argument("--ref", default=os.environ.get("GITHUB_REF", ""))
    generate.add_argument("--event", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    generate.add_argument("--workflow", default=os.environ.get("GITHUB_WORKFLOW", ""))
    generate.add_argument("--workflow-ref", default=os.environ.get("GITHUB_WORKFLOW_REF", ""))
    generate.add_argument("--workflow-sha", default=os.environ.get("GITHUB_WORKFLOW_SHA", ""))
    generate.add_argument("--run-id", type=int, default=int(os.environ.get("GITHUB_RUN_ID", "0")))
    generate.add_argument("--run-attempt", type=int, default=int(os.environ.get("GITHUB_RUN_ATTEMPT", "0")))
    generate.add_argument("--contract-result", required=True)
    generate.add_argument("--regression-result", required=True)
    generate.add_argument("--static-security-result", required=True)
    generate.add_argument("--deterministic-result", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("path", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            value = json.loads(args.path.read_text(encoding="utf-8"))
            if not isinstance(value, Mapping):
                raise ValueError("promotion evidence root must be an object")
            result = validate_promotion_evidence(value)
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "pass" else 1

        evidence = build_promotion_evidence(
            root=args.root,
            release_contract_path=args.release_contract,
            repository=args.repository,
            ref=args.ref,
            event=args.event,
            workflow=args.workflow,
            workflow_ref=args.workflow_ref,
            workflow_sha=args.workflow_sha,
            run_id=args.run_id,
            run_attempt=args.run_attempt,
            contract_result=args.contract_result,
            regression_result=args.regression_result,
            static_security_result=args.static_security_result,
            deterministic_result=args.deterministic_result,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"schema": "adk-promotion-evidence-generation/v1", "status": "pass", "out": str(args.out)}))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema": "adk-promotion-evidence-generation/v1", "status": "fail", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(_main())
