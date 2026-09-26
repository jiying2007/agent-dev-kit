#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$ROOT_DIR" <<'PY'
import importlib.util
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
workflow_dir = root / ".github/workflows"
workflow_files = sorted(workflow_dir.glob("*.yml"))
assert workflow_files, "no hosted workflows found"

consumer_files = sorted(workflow_dir.glob("*-consumer-contract.yml"))
consumer_validators = sorted((root / ".github/contracts").glob("*_consumer_contract.py"))
assert consumer_validators, "no consumer contract validators found"
expected_consumer_workflows = {
    f"{path.stem.removesuffix('_consumer_contract').replace('_', '-')}-consumer-contract.yml"
    for path in consumer_validators
}
assert {path.name for path in consumer_files} == expected_consumer_workflows, (
    consumer_files,
    consumer_validators,
)

# Every hosted workflow starts from an explicit read-only contents permission.
# Every checkout is read-only by construction: no persisted git credential may remain.
# Every hosted job must also have a bounded timeout so runner or third-party action
# hangs fail closed instead of consuming unbounded hosted capacity. External actions
# must use immutable full commit SHAs; repository-local actions remain allowed.
expected_write_permissions = {
    "branch-gc.yml": ["contents"],
    "ci.yml": ["id-token"],
    "release-tag-promotion.yml": ["artifact-metadata", "artifact-metadata", "attestations", "attestations", "contents", "contents", "contents", "id-token", "id-token"],
    "release.yml": ["artifact-metadata", "attestations", "contents", "id-token"],
    "security-codeql.yml": ["security-events"],
    "native-claude-conformance.yml": ["id-token"],
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
    secret_refs = sorted(set(re.findall(r"\$\{\{\s*secrets\.([A-Z0-9_]+)\s*\}\}", text)))
    expected_secret_refs = {
        "native-claude-conformance.yml": ["ANTHROPIC_API_KEY"],
    }
    assert secret_refs == expected_secret_refs.get(path.name, []), (
        path.name,
        secret_refs,
        "repository secrets are forbidden except for the reviewed real native campaign credential",
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

ci = (workflow_dir / "ci.yml").read_text(encoding="utf-8")
assert "  push:\n    branches:\n      - main\n  pull_request:\n" in ci, "core CI must push-trigger only on main"
assert "\n      - master\n" not in ci, "stale master push trigger must not return"

assert "- name: Validate PR source version advance" in ci, "PR CI must enforce source SemVer advance before merge"
assert "github.event.pull_request.base.sha" in ci, "version advance gate must bind the exact PR base SHA"
assert "matrix.python-version == '3.11'" in ci, "version advance gate must stay on required contract-py3.11"
assert "python -m agent_dev_kit.versioning require-advance" in ci, "PR version gate must use canonical typed SemVer authority"
assert "fetch-depth: 0" in ci.split("\n  regression:\n", 1)[0], "contract checkout must include the exact PR base commit"

platform = (workflow_dir / "platform.yml").read_text(encoding="utf-8")
assert platform.startswith("name: platform\n"), "Platform workflow display identity must stay stable"
assert "\n  platform-vnext:\n    name: platform-vnext\n" in platform, "ruleset-required platform-vnext check context must stay explicit"

promotion = ci.split("\n  promotion-evidence:\n", 1)[1]
assert "if: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}" in promotion, "promotion evidence must stay confined to main pushes"
assert "id-token: write" in promotion, "promotion OIDC permission must remain explicit"

wheel_upload = ci.split("      - name: Upload candidate wheel\n", 1)[1].split("\n  static-security:\n", 1)[0]
assert "if-no-files-found: error" in wheel_upload, "candidate wheel upload must fail closed"
timing_upload = ci.split("      - name: Upload timing evidence\n", 1)[1].split("\n  deterministic-eval-package:\n", 1)[0]
assert "if-no-files-found: ignore" in timing_upload, "regression timing upload must remain best-effort"

pr_cancellable = {
    workflow_dir / "ci.yml": "agent-dev-kit-ci-v2",
    workflow_dir / "security-codeql.yml": "security-codeql",
    workflow_dir / "platform.yml": "platform",
    workflow_dir / "digital-worker-contract.yml": "digital-worker-contract",
}
for path in consumer_files:
    pr_cancellable[path] = path.stem
for path, group in pr_cancellable.items():
    text = path.read_text(encoding="utf-8")
    assert "permissions:\n  contents: read\n" in text, path.name
    assert f"group: {group}-${{{{ github.event.pull_request.number || github.run_id }}}}" in text, path.name
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in text, path.name

for path in [*consumer_files, workflow_dir / "digital-worker-contract.yml"]:
    text = path.read_text(encoding="utf-8")
    assert "fetch-depth: 0" in text, path.name
    assert "fetch-tags: true" in text, path.name

branch_gc = (workflow_dir / "branch-gc.yml").read_text(encoding="utf-8")
assert "cancel-in-progress: false" in branch_gc, "branch-gc write/cleanup evidence must stay non-cancellable"
branch_gc_apply = branch_gc.split("\n  apply:\n", 1)[1]
assert "if: (github.event_name == 'push' && github.ref == 'refs/heads/main') || (github.event_name == 'workflow_dispatch' && inputs.apply && github.ref == 'refs/heads/main')" in branch_gc_apply, "branch-gc write apply must stay confined to main"
assert "contents: write" in branch_gc_apply, "branch-gc write permission must remain explicit"

release = (workflow_dir / "release.yml").read_text(encoding="utf-8")
assert "concurrency:" not in release, "release serialization semantics must remain unchanged"
assert "  workflow_dispatch:\n" in release, "tag-bound manual release entrypoint must remain available"
dispatch_block = release.split("\n  workflow_dispatch:\n", 1)[1].split("\n  workflow_call:\n", 1)[0]
assert "release_tag:" in dispatch_block and "release_commit:" in dispatch_block, "manual repair dispatch must require exact tag and commit"
assert "  workflow_call:\n" in release, "reviewed exact-tag reusable release entrypoint must be declared"
workflow_call_block = release.split("\n  workflow_call:\n", 1)[1].split("\n\npermissions:", 1)[0]
assert "release_tag:" in workflow_call_block and "release_commit:" in workflow_call_block, "reusable release must require exact tag and commit inputs"
assert "successful_main_ci_run_id:" in workflow_call_block, "reusable release must accept bounded successful-main CI evidence"
assert "type: number" in workflow_call_block and "default: 0" in workflow_call_block, "successful-main CI run ID must preserve GitHub numeric input typing"
assert "successful_main_ci_run_id:" not in dispatch_block, "manual dispatch must not expose the main-CI reuse input"
assert "actions: read" in release, "release must have bounded read permission to verify successful-main CI evidence"
assert "- name: Validate successful main CI reuse" in release, "release must independently verify CI reuse evidence"
assert '"name": "agent-dev-kit-ci"' in release, "release reuse must bind canonical CI workflow name"
assert '"status": "completed"' in release and '"conclusion": "success"' in release, "release reuse must require completed successful CI"
assert '"event": "push"' in release and '"head_branch": "main"' in release, "release reuse must require push-to-main CI"
assert '"head_sha": release_commit' in release, "release reuse must bind CI head SHA to release commit"
assert '"path": ".github/workflows/ci.yml"' in release, "release reuse must bind canonical CI workflow path"
assert "ref: ${{ inputs.release_commit || github.ref }}" in release, "reusable release checkout must bind exact requested commit"
assert "- name: Validate tag-bound release identity" in release, "release ref guard missing"
assert 'if [[ "$GITHUB_REF_TYPE" != "tag" || "$GITHUB_REF_NAME" != v* ]]; then' in release, "ordinary release must still fail closed off tag refs"
assert 'git fetch --force --no-tags origin "refs/tags/${CALLED_RELEASE_TAG}:refs/tags/${CALLED_RELEASE_TAG}"' in release, "reusable release must fetch the exact declared tag"
assert 'if [[ "$TAG_COMMIT" != "$CALLED_RELEASE_COMMIT" ]]; then' in release, "reusable release tag must peel to the exact declared commit"
assert 'EXPECTED_TAG="v${SOURCE_VERSION}"' in release, "release must derive expected tag from source version"
assert 'if [[ "$RELEASE_TAG" != "$EXPECTED_TAG" ]]; then' in release, "release tag must match source version"
assert "bash scripts/version-manager.sh verify" in release, "release must verify synchronized version identity before build work"
bootstrap_block = release.split("- name: Validate tag-bound release identity", 1)[1].split("- name: Install CI dependencies", 1)[0]
assert "version-manager.sh verify" not in bootstrap_block, "tag-bound bootstrap must remain stdlib-only before dependency install"
assert release.index("- name: Validate tag-bound release identity") < release.index("- name: Install CI dependencies"), "release identity guard must run before build/install work"
assert release.index("- name: Install CI dependencies") < release.index("- name: Validate synchronized source version identity") < release.index("- name: Validate and smoke"), "full version projection verification must run after dependencies and before smoke"
smoke_block = release.split("- name: Validate and smoke", 1)[1].split("- name: Build reproducible release", 1)[0]
assert 'VERIFIED_MAIN_CI_REUSE: ${{ steps.ci-reuse.outputs.verified_main_ci_reuse }}' in smoke_block, "release smoke must consume verified CI reuse output"
assert 'bash tests/run_all.sh --quick' in smoke_block, "verified main CI reuse must retain bounded regression smoke"
assert 'bash tests/run_all.sh' in smoke_block, "unverified release paths must retain full regression"
assert "- name: Validate complete release artifact bundle" in release, "release bundle completeness guard missing"
assert "archives=(dist/*.tar.gz)" in release, "release bundle must require one archive"
assert "checksums=(dist/*.tar.gz.sha256)" in release, "release bundle must require one matching checksum"
assert "sha256sum --check" in release, "release sidecar checksum must be verified"
assert "if-no-files-found: error" in release, "release artifact upload must fail closed when files are missing"
assert "- name: Publish GitHub Release" in release, "validated release bundle must be published to GitHub Releases"
assert 'gh release create "$RELEASE_TAG"' in release, "GitHub Release creation command missing"
assert 'gh release download "$RELEASE_TAG"' in release, "existing GitHub Release retry must download assets for verification"
assert 'cmp "$archive"' in release and 'cmp "$checksum"' in release and 'cmp "$contract"' in release, "existing release assets must be byte-compared"
assert "published GitHub Release is not immutable" in release, "release workflow must fail closed if repository immutability is disabled"
assert "remote release digest mismatch for $asset_name" in release, "release workflow must verify remote GitHub asset digests"
assert "GitHub Release immutable asset digests verified" in release, "release workflow must record final immutable remote digest verification"

release_tag_promotion = (workflow_dir / "release-tag-promotion.yml").read_text(encoding="utf-8")
assert "  workflow_run:\n" in release_tag_promotion, "release tag promotion must be completion-triggered"
assert "      - agent-dev-kit-ci\n" in release_tag_promotion, "release tag promotion must depend on canonical main CI"
assert "github.event.workflow_run.conclusion == 'success'" in release_tag_promotion, "release tag promotion requires successful CI"
assert "github.event.workflow_run.event == 'push'" in release_tag_promotion, "release tag promotion requires a push CI run"
assert "github.event.workflow_run.head_branch == 'main'" in release_tag_promotion, "release tag promotion must stay confined to main"
assert "cancel-in-progress: false" in release_tag_promotion, "release tag promotion must be non-cancellable"
assert "contents: write" in release_tag_promotion, "tag creation permission must remain explicit and reviewed"
assert "git ls-remote origin refs/heads/main" in release_tag_promotion, "tag promotion must re-check exact current main"
assert "bash scripts/version-manager.sh verify" in release_tag_promotion, "tag promotion must verify synchronized version identity"
assert 'request(\n                  "/git/tags",' in release_tag_promotion, "tag promotion must create an annotated tag object"
assert 'payload={"ref": f"refs/tags/{tag}", "sha": tag_object["sha"]}' in release_tag_promotion, "tag promotion must point the version ref at the annotated tag object"
assert 'promotion_status = "created-annotated"' in release_tag_promotion, "new version tags must be recorded as annotated promotions"
assert 'promotion_status = "source-version-tag-conflict"' in release_tag_promotion, "mismatched existing version tags must fail closed"
assert 'promotion_status = "version-already-released"' not in release_tag_promotion, "version/tag conflicts must not be converted into successful skips"
assert 'if: ${{ always() }}' in release_tag_promotion, "tag-conflict evidence must still upload on promotion failure"
assert "uses: ./.github/workflows/release.yml" in release_tag_promotion, "tag promotion must reuse the canonical release workflow"
current_release_block = release_tag_promotion.split("\n  release:\n", 1)[1].split("\n\n  discover-orphaned-releases:", 1)[0]
repair_release_block = release_tag_promotion.split("\n  repair-orphaned-release:\n", 1)[1]
assert "actions: read" in current_release_block, "current release must allow bounded workflow-run verification"
assert "successful_main_ci_run_id: ${{ github.event.workflow_run.id }}" in current_release_block, "current release must forward the exact successful-main CI run"
assert "actions: read" in repair_release_block, "orphan repair caller must satisfy reusable workflow permission floor"
assert "successful_main_ci_run_id:" not in repair_release_block, "orphan repair must not reuse unrelated current-main CI evidence"
assert "needs.promote-tag.outputs.release_needed == 'true'" in release_tag_promotion, "canonical release must run only for an exact newly promoted or retryable tag"
assert "  discover-orphaned-releases:\n" in release_tag_promotion, "promotion must audit immutable v7 release continuity"
assert "RELEASE_REPAIR_BASELINE: 7.0.0" in release_tag_promotion, "self-heal baseline must start at the immutable v7 release contract"
assert 'release.get("immutable") is not True' in release_tag_promotion, "existing v7 releases must remain immutable"
assert "actual_assets != expected_assets" in release_tag_promotion, "existing v7 release asset sets must be audited"
assert "def release_assets(release: object)" in release_tag_promotion, "orphan audit must load assets from the dedicated release-assets endpoint"
assert 'f"{api_root}/releases/{release_id}/assets?per_page=100"' in release_tag_promotion, "orphan audit must use the release id asset endpoint"
assert 'release.get("assets", [])' not in release_tag_promotion, "orphan audit must not trust the embedded release assets field"
assert "source version mismatch" in release_tag_promotion, "orphan discovery must bind tag to source version"
assert "release tag must be annotated" in release_tag_promotion, "v7 release tags must remain annotated"
assert "  repair-orphaned-release:\n" in release_tag_promotion, "tagged-but-unreleased versions must have an automatic repair path"
assert "fromJSON(needs.discover-orphaned-releases.outputs.repairs)" in release_tag_promotion, "repair matrix must come from audited exact-tag evidence"
assert release_tag_promotion.count("uses: ./.github/workflows/release.yml") == 2, "current release and orphan repair must share the canonical release workflow"

native_campaign = (workflow_dir / "native-claude-conformance.yml").read_text(encoding="utf-8")
native_trigger = native_campaign.split("permissions:", 1)[0]
assert "workflow_dispatch:" in native_trigger, "real native campaign must be explicitly dispatched"
assert "pull_request:" not in native_trigger and "push:" not in native_trigger and "schedule:" not in native_trigger, "real native campaign must never run automatically from source events"
assert "RUN_REAL_NATIVE" in native_campaign, "real native campaign requires an explicit confirmation token"
assert "claude_code_version:" in native_campaign and "model:" in native_campaign, "real native campaign must pin runtime and model inputs"
assert "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" in native_campaign, "hosted campaign must install the exact requested Claude Code version"
assert "ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}" in native_campaign, "hosted campaign must use the reviewed GitHub secret name"
assert '"apiKeyHelper"' in native_campaign, "provider secret must be bridged through the isolated user-level helper"
assert "--auth-mode home" in native_campaign, "native runner must preserve only the reviewed HOME auth surface"
assert native_campaign.count("native-campaign prepare") == 1
assert native_campaign.count("native-campaign run") == 1
assert native_campaign.count("native-campaign finalize") == 1
assert "cosign sign-blob" in native_campaign and "cosign verify-blob" in native_campaign, "retained receipt must be signed and immediately verified"
assert "production-loader.json" in native_campaign, "candidate package must prove production-loader verification"
assert '"target_promotion_performed": False' in native_campaign
assert '"registry_promotion_performed": False' in native_campaign
assert '"release_authorized": False' in native_campaign
assert "gh pr create" not in native_campaign and "git push" not in native_campaign, "real campaign evidence lane must not mutate repository lifecycle state"
assert "contents: write" not in native_campaign, "real campaign must not gain repository write authority"

dependency_review = (workflow_dir / "security-dependency-review.yml").read_text(encoding="utf-8")
assert "pull_request:" in dependency_review, "dependency review must remain PR-only"
assert "cancel-in-progress: true" in dependency_review, "PR-only dependency review may cancel superseded runs"

governance_path = root / "tools/control_plane/github_governance.py"
spec = importlib.util.spec_from_file_location("adk_github_governance", governance_path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

required = module.DEFAULT_REQUIRED_CHECKS
passing_repo = {
    "full_name": "example/agent-dev-kit",
    "default_branch": "main",
    "allow_squash_merge": True,
    "allow_merge_commit": False,
    "allow_rebase_merge": False,
    "delete_branch_on_merge": True,
}
passing_branch = {"name": "main", "protected": True}
passing_ruleset = {
    "id": 1,
    "name": "main-governance",
    "target": "branch",
    "enforcement": "active",
    "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
    "bypass_actors": [],
    "rules": [
        {
            "type": "pull_request",
            "parameters": {
                "allowed_merge_methods": ["squash"],
                "required_approving_review_count": 0,
            },
        },
        {
            "type": "required_status_checks",
            "parameters": {
                "required_status_checks": [
                    {"context": context, "integration_id": None}
                    for context in required
                ],
                "strict_required_status_checks_policy": True,
            },
        },
        {"type": "non_fast_forward"},
        {"type": "deletion"},
    ],
}
passing = module.evaluate_state(
    passing_repo,
    passing_branch,
    [passing_ruleset],
    branch_name="main",
)
assert passing["compliant"] is True, passing
assert passing["missing_status_checks"] == [], passing
assert passing["checks"]["solo_zero_required_approvals"] is True, passing
assert passing["checks"]["no_ruleset_bypass"] is True, passing
assert passing["checks"]["strict_required_status_checks"] is True, passing

failing_repo = dict(passing_repo)
failing_repo["allow_merge_commit"] = True
failing = module.evaluate_state(
    failing_repo,
    {"name": "main", "protected": False},
    [],
    branch_name="main",
)
assert failing["compliant"] is False, failing
assert "contract-py3.11" in failing["missing_status_checks"], failing
assert "repository merge methods are not squash-only" in failing["violations"], failing
assert failing["remediation"], failing

governance_workflow = (workflow_dir / "github-governance-control-plane.yml").read_text(encoding="utf-8")
trigger_block = governance_workflow.split("permissions:", 1)[0]
assert "workflow_dispatch:" in trigger_block, "governance evidence must remain manually triggered"
assert "pull_request:" not in trigger_block and "push:" not in trigger_block, "known external blocker must not poison core CI"
assert "GH_TOKEN: ${{ github.token }}" in governance_workflow, "governance verifier must use ephemeral GitHub token"
assert "--out \"$RUNNER_TEMP/github-governance-report.json\"" in governance_workflow, "governance evidence report path missing"
assert "if: always()" in governance_workflow, "governance report must upload even when verification fails"
assert "if-no-files-found: error" in governance_workflow, "governance evidence upload must fail closed"
PY

bash "$ROOT_DIR/tests/test_github_governance_admin.sh"
echo "[PASS] hosted workflow hygiene"
