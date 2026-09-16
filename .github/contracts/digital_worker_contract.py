#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "manifests/integrations/digital-worker.json"
CODEX_BINDING = ROOT / "manifests/integrations/codex-runtime-binding.json"
WORKFLOW = ROOT / ".github/workflows/digital-worker-contract.yml"

EXPECTED_BASELINE = {
    "version": "5.1.1",
    "tag": "v5.1.1",
    "commit": "e36dfec69f21806431b07daddc4bd78412179e62",
    "tree": "9c37468930231bdfa7f230e38ed1b85e0dc0f5f5",
    "manifest_blob": "4715a03db12ac28d2978356306381c028c75af76",
    "release_artifact_sha256": "1924d79034a216f04dde0d08826dd5b87c597f090721335c1cec16e9bc88cbc1",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    require(CONTRACT.is_file(), "missing digital-worker integration contract")
    require(CODEX_BINDING.is_file(), "missing Codex runtime-binding contract")
    require(WORKFLOW.is_file(), "missing digital-worker contract workflow")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    binding = json.loads(CODEX_BINDING.read_text(encoding="utf-8"))

    require(set(contract) == {
        "schema", "contract_version", "status", "consumer", "provider", "role",
        "asset_profile", "release_baseline", "consumer_owns", "provider_owns",
        "identity_contract", "delivery", "must_not", "skill_ownership_rule",
        "maturity_boundary",
    }, "digital-worker integration contract must use the closed v2 schema")
    require(contract["schema"] == "adk-digital-worker-integration/v2", "digital-worker integration schema drift")
    require(contract["contract_version"] == "2.0", "digital-worker integration contract version drift")
    require(contract["status"] == "active", "digital-worker integration contract must be active")
    require(contract["consumer"] == "jiying2007/digital-worker", "digital-worker consumer identity drift")
    require(contract["provider"] == "jiying2007/agent-dev-kit", "ADK provider identity drift")
    require(contract["role"] == "agent-asset-control-plane", "digital-worker integration role drift")
    require(contract["asset_profile"] == "embedded-fullstack", "digital-worker asset profile drift")
    require(contract["release_baseline"] == EXPECTED_BASELINE, "digital-worker release baseline drift")
    require(binding["release_baseline"] == EXPECTED_BASELINE, "digital-worker and Codex must share one immutable ADK release baseline")

    identity = contract["identity_contract"]
    require(identity == {
        "canonical_provider_repository": "jiying2007/agent-dev-kit",
        "release_baseline_is_immutable": True,
        "consumer_must_bind_exact_release_commit": True,
        "consumer_records_refs_not_asset_copies": True,
        "runtime_binding_owns_exact_source_selection": True,
        "runtime_profile_is_separate_from_asset_profile": True,
        "monolithic_runtime_bundle_is_not_required_identity": True,
    }, "digital-worker identity contract drift")

    delivery = contract["delivery"]
    require(delivery["mode"] == "exact-source-set-reference", "digital-worker delivery mode drift")
    require(delivery["provider_produces_monolithic_runtime_bundle"] is False, "ADK must not produce a monolithic runtime bundle")
    require(delivery["runtime_binding_selects_exact_source_set"] is True, "Runtime Binding must own exact source selection")
    require(delivery["runtime_binding_assembles_runtime_distribution"] is True, "Runtime Binding must assemble runtime distribution")
    require(delivery["direct_live_home_write"] is False, "ADK must not write live runtime home")
    require(delivery["plan_before_apply"] is True, "runtime delivery must plan before apply")
    require(delivery["receipt_required"] is True and delivery["rollback_required"] is True, "runtime delivery must preserve receipt/rollback")

    rendered = CONTRACT.read_text(encoding="utf-8")
    for retired in (
        '"asset_bundle_hash"', "BLOCKED_ASSET_BUNDLE_IDENTITY", "5.0.0-rc.2",
        "provider-produced bundle", "target_export_contract",
    ):
        require(retired not in rendered, f"retired digital-worker bundle compatibility returned: {retired}")

    baseline = contract["release_baseline"]
    require(re.fullmatch(r"[0-9a-f]{40}", baseline["commit"]) is not None, "release commit must be exact")
    require(re.fullmatch(r"[0-9a-f]{40}", baseline["tree"]) is not None, "release tree must be exact")
    require(re.fullmatch(r"[0-9a-f]{40}", baseline["manifest_blob"]) is not None, "manifest blob must be exact")
    require(re.fullmatch(r"[0-9a-f]{64}", baseline["release_artifact_sha256"]) is not None, "release artifact digest must be SHA-256")
    require(git("rev-parse", f"{baseline['commit']}^{{tree}}") == baseline["tree"], "release baseline tree mismatch")
    require(git("rev-parse", f"{baseline['commit']}:manifest.json") == baseline["manifest_blob"], "release manifest blob mismatch")
    require(git("rev-parse", f"{baseline['tag']}^{{}}") == baseline["commit"], "release tag does not peel to baseline commit")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("runs-on: ubuntu-24.04" in workflow and "ubuntu-latest" not in workflow, "digital-worker contract runner must be pinned")
    for lineno, line in enumerate(workflow.splitlines(), 1):
        match = re.search(r"\buses:\s*[^\s@]+@([^\s#]+)", line)
        if match:
            require(re.fullmatch(r"[0-9a-f]{40}", match.group(1)) is not None, f"workflow action must be SHA-pinned at line {lineno}")

    print("Digital Worker terminal asset contract PASS")
    print(f"release_baseline={baseline['version']}@{baseline['commit']}")
    print("delivery=exact-source-set-reference")


if __name__ == "__main__":
    main()
