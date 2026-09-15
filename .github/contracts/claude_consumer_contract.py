#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BINDING = ROOT / "manifests/integrations/claude-runtime-binding.json"
WORKFLOW = ROOT / ".github/workflows/claude-consumer-contract.yml"

EXPECTED_BASELINE = {
    "version": "5.1.0",
    "tag": "v5.1.0",
    "commit": "59cbd5cb40ca7077ee5407636bfc617e295ec7e5",
    "tree": "16d3c99d4dac8c41c09509b82c536a11cc058ca9",
    "manifest_blob": "bc349b0dc003c553059cdddbc368ae8ea6ffda89",
    "release_artifact_sha256": "d4684fe5888203b4a25e7dda9ab51b83fb900cae2d09adb6e5179a775748c965",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    require(BINDING.is_file(), "missing Claude runtime binding")
    require(WORKFLOW.is_file(), "missing Claude consumer workflow")
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    require(set(binding) == {
        "schema", "contract_version", "status", "consumer", "provider", "role",
        "runtime_target", "asset_profile", "release_baseline", "provider_owns",
        "consumer_owns", "identity_contract", "delivery", "must_not", "maturity_boundary",
    }, "Claude binding must use the closed consumer schema")
    require(binding["schema"] == "adk-claude-runtime-binding/v1", "Claude binding schema drift")
    require(binding["contract_version"] == "1.0", "Claude binding contract version drift")
    require(binding["status"] == "active", "Claude handoff contract must be active")
    require(binding["consumer"] == "jiying2007/claude", "Claude consumer drift")
    require(binding["provider"] == "jiying2007/agent-dev-kit", "ADK provider drift")
    require(binding["role"] == "exact-source-set-handoff", "Claude handoff role drift")
    require(binding["runtime_target"] == "claude-code", "Claude runtime target drift")
    require(binding["asset_profile"] == "embedded-fullstack", "Claude asset profile drift")
    require(binding["release_baseline"] == EXPECTED_BASELINE, "immutable 5.1 release baseline drift")
    require(binding["identity_contract"] == {
        "canonical_provider_repository": "jiying2007/agent-dev-kit",
        "release_baseline_is_immutable": True,
        "consumer_must_bind_exact_release_commit": True,
        "consumer_must_bind_exact_source_blob_per_vendored_asset": True,
        "consumer_must_preserve_asset_profile": True,
        "runtime_profile_is_separate_from_asset_profile": True,
    }, "Claude identity contract drift")
    delivery = binding["delivery"]
    require(delivery["mode"] == "exact-source-set", "Claude delivery mode drift")
    require(delivery["provider_produces_monolithic_claude_bundle"] is False, "ADK must not own Claude bundle assembly")
    require(delivery["consumer_assembles_runtime_distribution"] is True, "Claude must own runtime distribution assembly")
    require(delivery["direct_live_home_write"] is False, "ADK must not write Claude live home")
    require(delivery["plan_before_apply"] is True and delivery["dry_run_before_apply"] is True, "Claude delivery must retain plan/dry-run gates")
    require(delivery["receipt_required"] is True and delivery["rollback_required"] is True, "Claude delivery must retain receipt/rollback")
    text = BINDING.read_text(encoding="utf-8")
    for token in ("asset_bundle_hash", "verification_pass", "domain_gate_pass", "release_ready"):
        require(token not in text, f"forbidden runtime/domain claim entered Claude handoff: {token}")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("runs-on: ubuntu-24.04" in workflow and "ubuntu-latest" not in workflow, "Claude consumer runner must be pinned")
    for lineno, line in enumerate(workflow.splitlines(), 1):
        match = re.search(r"\buses:\s*[^\s@]+@([^\s#]+)", line)
        if match:
            require(re.fullmatch(r"[0-9a-f]{40}", match.group(1)) is not None, f"workflow action must be SHA-pinned at line {lineno}")
    baseline = binding["release_baseline"]
    require(re.fullmatch(r"[0-9a-f]{40}", baseline["commit"]) is not None, "release commit must be exact")
    require(re.fullmatch(r"[0-9a-f]{40}", baseline["tree"]) is not None, "release tree must be exact")
    require(re.fullmatch(r"[0-9a-f]{40}", baseline["manifest_blob"]) is not None, "manifest blob must be exact")
    require(re.fullmatch(r"[0-9a-f]{64}", baseline["release_artifact_sha256"]) is not None, "release artifact digest must be SHA-256")
    require(git("rev-parse", f"{baseline['commit']}^{{tree}}") == baseline["tree"], "release baseline tree does not match commit")
    require(git("rev-parse", f"{baseline['commit']}:manifest.json") == baseline["manifest_blob"], "release baseline manifest blob mismatch")
    require(git("rev-parse", f"{baseline['tag']}^{{}}") == baseline["commit"], "release tag does not peel to baseline commit")
    print("Claude consumer contract PASS")
    print(f"release_baseline={baseline['version']}@{baseline['commit']}")
    print("delivery=exact-source-set")
    print("maturity=handoff-only-r1-ready-not-r2")


if __name__ == "__main__":
    main()
