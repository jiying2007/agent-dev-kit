#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$ROOT_DIR" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
workflow_dir = root / ".github/workflows"
workflow_files = sorted(workflow_dir.glob("*.yml"))
assert workflow_files, "no hosted workflows found"

consumer_files = sorted(workflow_dir.glob("*-consumer-contract.yml"))
assert len(consumer_files) == 1, consumer_files

# Every hosted workflow starts from an explicit read-only contents permission.
# Every checkout is read-only by construction: no persisted git credential may remain.
# Every hosted job must also have a bounded timeout so runner or third-party action
# hangs fail closed instead of consuming unbounded hosted capacity. External actions
# must use immutable full commit SHAs; repository-local actions remain allowed.
expected_write_permissions = {
    "branch-gc.yml": ["contents"],
    "ci.yml": ["id-token"],
    "release.yml": ["artifact-metadata", "attestations", "id-token"],
    "security-codeql.yml": ["security-events"],
}
for path in workflow_files:
    text = path.read_text(encoding="utf-8")
    assert "permissions:\n  contents: read\n" in text, (
        path.name,
        "hosted workflows must declare a read-only root contents permission",
    )
    assert "pull_request_target:" not in text, (
        path.name,
        "pull_request_target is not allowed in hosted workflows",
    )
    assert not re.search(r"(?m)^\s*permissions:\s*(?:read-all|write-all)\s*$", text), (
        path.name,
        "permission shorthands bypass the reviewed explicit permission map",
    )
    assert not re.search(r"(?m)^\s*permissions:\s*\{", text), (
        path.name,
        "inline permission maps are not allowed; use reviewed block mappings",
    )
    # Hosted CI stays secretless and fail-closed: keyless OIDC/GITHUB_TOKEN replace
    # repository secrets, while explicit failure masking cannot weaken qualification.
    assert not re.search(r"\$\{\{\s*secrets\.", text), (
        path.name,
        "hosted workflows must not depend on repository secrets",
    )
    assert "continue-on-error:" not in text, (
        path.name,
        "hosted qualification steps must not suppress failures",
    )
    assert not re.search(r"\|\|\s*true\b", text), (
        path.name,
        "shell failure masking with '|| true' is not allowed",
    )
    assert not re.search(r"(?m)^\s*set\s+\+e(?:\s|$)", text), (
        path.name,
        "shell error handling must remain fail-closed",
    )
    checkout_count = text.count("uses: actions/checkout@")
    credential_count = text.count("persist-credentials: false")
    assert credential_count == checkout_count, (
        path.name,
        checkout_count,
        credential_count,
    )

    job_count = text.count("runs-on:")
    timeout_values = [
        int(value)
        for value in re.findall(r"(?m)^\s+timeout-minutes:\s+(\d+)\s*$", text)
    ]
    assert len(timeout_values) == job_count, (
        path.name,
        job_count,
        timeout_values,
    )
    assert all(5 <= value <= 45 for value in timeout_values), (
        path.name,
        timeout_values,
    )

    action_uses = re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", text)
    for action in action_uses:
        action = action.strip("'\"")
        if action.startswith("./"):
            continue
        assert "@" in action, (path.name, action)
        ref = action.rsplit("@", 1)[1]
        assert re.fullmatch(r"[0-9a-f]{40}", ref), (
            path.name,
            action,
            "external actions must be pinned to a full 40-hex commit SHA",
        )

    write_permissions = sorted(
        re.findall(r"(?m)^\s+([a-z0-9-]+):\s+write\s*$", text)
    )
    assert write_permissions == expected_write_permissions.get(path.name, []), (
        path.name,
        write_permissions,
        "workflow write permissions must match the reviewed allowlist",
    )

# Core CI has one canonical push branch. Do not reintroduce historical branch aliases
# that no longer exist in repository metadata.
ci = (workflow_dir / "ci.yml").read_text(encoding="utf-8")
assert "  push:\n    branches:\n      - main\n  pull_request:\n" in ci, "core CI must push-trigger only on main"
assert "\n      - master\n" not in ci, "stale master push trigger must not return"

# Build artifacts are release-like evidence and must fail closed when absent; regression
# timing remains diagnostic best-effort evidence and intentionally stays non-blocking.
wheel_upload = ci.split("      - name: Upload candidate wheel\n", 1)[1].split("\n  static-security:\n", 1)[0]
assert "if-no-files-found: error" in wheel_upload, "candidate wheel upload must fail closed"
timing_upload = ci.split("      - name: Upload timing evidence\n", 1)[1].split("\n  deterministic-eval-package:\n", 1)[0]
assert "if-no-files-found: ignore" in timing_upload, "regression timing upload must remain best-effort"

# Superseded-run cancellation is safe only for PR validation. Non-PR runs must be
# isolated by run_id so fresh-main, scheduled, and manual evidence cannot cancel.
pr_cancellable = {
    workflow_dir / "ci.yml": "agent-dev-kit-ci-v2",
    workflow_dir / "security-codeql.yml": "security-codeql",
    workflow_dir / "platform-vnext.yml": "platform-vnext",
    workflow_dir / "digital-worker-contract.yml": "digital-worker-contract",
    consumer_files[0]: consumer_files[0].stem,
}
for path, group in pr_cancellable.items():
    text = path.read_text(encoding="utf-8")
    assert "permissions:\n  contents: read\n" in text, path.name
    assert f"group: {group}-${{{{ github.event.pull_request.number || github.run_id }}}}" in text, path.name
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in text, path.name

for path in (consumer_files[0], workflow_dir / "digital-worker-contract.yml"):
    text = path.read_text(encoding="utf-8")
    assert "fetch-depth: 0" in text, path.name
    assert "fetch-tags: true" in text, path.name

branch_gc = (workflow_dir / "branch-gc.yml").read_text(encoding="utf-8")
assert "cancel-in-progress: false" in branch_gc, "branch-gc write/cleanup evidence must stay non-cancellable"

release = (workflow_dir / "release.yml").read_text(encoding="utf-8")
assert "concurrency:" not in release, "release serialization semantics must remain unchanged"
assert "  workflow_dispatch:\n" in release, "tag-bound manual release entrypoint must remain available"
assert "- name: Validate tag-bound release identity" in release, "release ref guard missing"
assert 'if [[ "$GITHUB_REF_TYPE" != "tag" || "$GITHUB_REF_NAME" != v* ]]; then' in release, "release must fail closed off tag refs"
assert 'EXPECTED_TAG="v${SOURCE_VERSION}"' in release, "release must derive expected tag from source version"
assert 'if [[ "$GITHUB_REF_NAME" != "$EXPECTED_TAG" ]]; then' in release, "release tag must match source version"
assert "- name: Validate complete release artifact bundle" in release, "release bundle completeness guard missing"
assert "archives=(dist/*.tar.gz)" in release, "release bundle must require one archive"
assert "checksums=(dist/*.tar.gz.sha256)" in release, "release bundle must require one matching checksum"
assert "sha256sum --check" in release, "release sidecar checksum must be verified"
assert "if-no-files-found: error" in release, "release artifact upload must fail closed when files are missing"

# Dependency review remains a PR-only supply-chain gate.
dependency_review = (workflow_dir / "security-dependency-review.yml").read_text(encoding="utf-8")
assert "pull_request:" in dependency_review, "dependency review must remain PR-only"
assert "cancel-in-progress: true" in dependency_review, "PR-only dependency review may cancel superseded runs"
PY

echo "[PASS] hosted workflow hygiene"
