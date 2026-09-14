#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$ROOT_DIR" <<'PY'
import importlib.util
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
control_plane = root / "tools/control_plane"
sys.path.insert(0, str(control_plane))
admin_path = control_plane / "github_governance_admin.py"
spec = importlib.util.spec_from_file_location("adk_github_governance_admin", admin_path)
assert spec is not None and spec.loader is not None
admin = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = admin
spec.loader.exec_module(admin)

required = admin.DEFAULT_REQUIRED_CHECKS
desired = admin.desired_ruleset_payload("main", admin.DEFAULT_RULESET_NAME, required)
rule_types = [rule["type"] for rule in desired["rules"]]
assert rule_types == ["pull_request", "required_status_checks", "non_fast_forward", "deletion"]
assert desired["conditions"]["ref_name"]["include"] == ["refs/heads/main"]
pull_request = desired["rules"][0]["parameters"]
assert pull_request["allowed_merge_methods"] == ["squash"]
assert pull_request["required_approving_review_count"] == 0
status_checks = desired["rules"][1]["parameters"]
assert [item["context"] for item in status_checks["required_status_checks"]] == list(required)
assert status_checks["strict_required_status_checks_policy"] is False

failing_repo = {
    "full_name": "example/agent-dev-kit",
    "default_branch": "main",
    "allow_squash_merge": True,
    "allow_merge_commit": True,
    "allow_rebase_merge": True,
    "delete_branch_on_merge": True,
}
failing_plan = admin.build_plan(
    failing_repo,
    {"name": "main", "protected": False},
    [],
    branch="main",
    ruleset_name=admin.DEFAULT_RULESET_NAME,
)
assert failing_plan["ruleset"]["action"] == "create", failing_plan
assert set(failing_plan["repository_changes"]) == {
    "allow_merge_commit",
    "allow_rebase_merge",
}, failing_plan
assert failing_plan["current_governance"]["compliant"] is False

compliant_repo = {
    **failing_repo,
    "allow_merge_commit": False,
    "allow_rebase_merge": False,
}
managed = json.loads(json.dumps(desired))
managed["id"] = 42
compliant_plan = admin.build_plan(
    compliant_repo,
    {"name": "main", "protected": True},
    [managed],
    branch="main",
    ruleset_name=admin.DEFAULT_RULESET_NAME,
)
assert compliant_plan["repository_changes"] == {}, compliant_plan
assert compliant_plan["ruleset"]["action"] == "none", compliant_plan
assert compliant_plan["current_governance"]["compliant"] is True, compliant_plan

drifted = json.loads(json.dumps(managed))
drifted["rules"][0]["parameters"]["allowed_merge_methods"] = ["merge", "squash"]
update_plan = admin.build_plan(
    compliant_repo,
    {"name": "main", "protected": True},
    [drifted],
    branch="main",
    ruleset_name=admin.DEFAULT_RULESET_NAME,
)
assert update_plan["ruleset"]["action"] == "update", update_plan
assert update_plan["ruleset"]["id"] == 42, update_plan

class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def request(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == "POST" and path.endswith("/rulesets"):
            return {"id": 77}
        return {}

fake = FakeClient()
operations = admin.apply_plan(fake, "example/agent-dev-kit", failing_plan)
assert [operation["operation"] for operation in operations] == [
    "update_repository",
    "create_ruleset",
], operations
assert [call[0] for call in fake.calls] == ["PATCH", "POST"], fake.calls
assert fake.calls[0][1] == "/repos/example/agent-dev-kit"
assert fake.calls[1][1] == "/repos/example/agent-dev-kit/rulesets"

fake_update = FakeClient()
update_operations = admin.apply_plan(fake_update, "example/agent-dev-kit", update_plan)
assert [operation["operation"] for operation in update_operations] == ["update_ruleset"]
assert fake_update.calls[0][0:2] == (
    "PUT",
    "/repos/example/agent-dev-kit/rulesets/42",
)

source = admin_path.read_text(encoding="utf-8")
assert "ADK_GITHUB_ADMIN_TOKEN" in source
assert "--apply refuses to run inside GitHub Actions" in source
assert "Administration write" in source
PY

echo "[PASS] GitHub governance admin remediation"
