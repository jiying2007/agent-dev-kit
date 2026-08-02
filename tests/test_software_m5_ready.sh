#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

bash "$ROOT_DIR/scripts/devkit.sh" help | rg -q 'doctor'
bash "$ROOT_DIR/scripts/devkit.sh" help | rg -q 'lock'
bash "$ROOT_DIR/scripts/devkit.sh" eval campaign --help >/dev/null
bash "$ROOT_DIR/scripts/devkit.sh" release rehearse --help >/dev/null
doctor_rc=0
bash "$ROOT_DIR/scripts/devkit.sh" doctor --summary-json >"$TMP_DIR/doctor.json" || doctor_rc=$?
[[ "$doctor_rc" -eq 0 || "$doctor_rc" -eq 1 ]] || {
  echo "[FAIL] doctor returned unexpected exit code: $doctor_rc" >&2
  exit 1
}

PYTHONPATH="$ROOT_DIR/src" python3 - "$ROOT_DIR" "$TMP_DIR" <<'PY'
import io
import hashlib
import json
import multiprocessing
import os
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from unittest import mock

from agent_dev_kit.campaign import (
    campaign_markdown,
    campaign_plan,
    check_campaign,
    load_campaign_contract,
    run_campaign,
)
from agent_dev_kit.doctor import run_doctor
from agent_dev_kit import campaign, evaluation, installer
from agent_dev_kit.evaluation import _claude_usage, run_deterministic
from agent_dev_kit.installer import RECEIPT_NAME, apply_plan, create_plan, rollback, write_plan
from agent_dev_kit.locking import TargetLock, clear_target_lock, target_lock_status
from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.release import _extract_release, _prerelease_is_newer, check_release

root = Path(os.sys.argv[1])
temp_root = Path(os.sys.argv[2])
manifest = Manifest.load(root)
assert manifest.version == "3.1.0-rc.7", manifest.version
assert check_release(manifest)["status"] == "pass"
assert _prerelease_is_newer("3.0.0", "3.1.0-rc.1")
assert _prerelease_is_newer("3.1.0-rc.1", "3.1.0-rc.2")
assert _prerelease_is_newer("3.1.0-rc.3", "3.1.0-rc.4")
assert _prerelease_is_newer("3.1.0-rc.4", "3.1.0-rc.5")
assert _prerelease_is_newer("3.1.0-rc.5", "3.1.0-rc.6")
assert _prerelease_is_newer("3.1.0-rc.6", "3.1.0-rc.7")
assert _prerelease_is_newer("3.1.0-rc.7", "3.1.0")
assert not _prerelease_is_newer("3.1.0", "3.1.0-rc.7")

contract_path = root / "manifests/software_m5_eval_contract_rc7.json"
contract, tasks_path, tasks = load_campaign_contract(manifest, contract_path)
assert len(tasks) == 60
assert len({task["id"] for task in tasks}) == 60
assert contract["trials"] == 3
assert contract["max_budget_usd"] == 150.0
assert contract["max_claude_call_usd"] == 0.2
skill_names = {item["name"] for item in manifest.data["skills"]}
generic_categories = {
    "routing", "context", "requirements", "planning", "orchestration", "git",
    "architecture", "test", "quality", "debug", "verification", "learning",
    "memory", "archive", "repository", "review", "embedded", "release",
}
assert all(task["expected_skill"] in skill_names for task in tasks)
assert all(task["category"] in generic_categories for task in tasks)
deterministic = run_deterministic(manifest, tasks)
assert deterministic["status"] == "pass", deterministic
assert deterministic["passed"] == 60
assert deterministic["latency"]["p95_ms"] < 20.0, deterministic["latency"]
assert match_text(manifest, "子代理驱动开发并复审")["skill"] == "adk-parallel-agent-governance"

claude_usage = _claude_usage(
    {
        "usage": {
            "input_tokens": 10,
            "cache_read_input_tokens": 20,
            "cache_creation_input_tokens": 30,
            "output_tokens": 40,
        }
    }
)
assert claude_usage["cache_creation_input_tokens"] == 30
assert claude_usage["total_tokens"] == 100

with mock.patch("agent_dev_kit.evaluation.shutil.which", return_value="/fixture/codex"), mock.patch(
    "agent_dev_kit.evaluation.subprocess.run",
    side_effect=subprocess.TimeoutExpired(["codex", "exec"], evaluation.RUNTIME_TIMEOUT_SECONDS),
):
    try:
        evaluation._run_codex(temp_root, "system", "prompt", temp_root / "schema.json")
    except ManifestError as exc:
        assert "timed out" in str(exc)
    else:
        raise AssertionError("runtime timeout did not fail closed")

def ready_plan(runtime, condition, task_count):
    return {
        "schema_version": 1,
        "status": "planned",
        "runtime": runtime,
        "runtime_version": runtime + "-fixture-1",
        "condition": condition,
        "tasks": task_count,
        "executable": "/fixture/" + runtime,
        "permissions": "read-only/no-tools",
        "reason": None,
    }

with mock.patch("agent_dev_kit.campaign.runtime_plan", side_effect=ready_plan):
    plan = campaign_plan(manifest, contract_path)
assert plan["status"] == "ready", plan
assert plan["primary_claude_calls"] == 360, plan
assert plan["maximum_claude_calls"] == 720, plan
assert plan["primary_worst_cost_usd"] == 72.0, plan
assert plan["maximum_worst_cost_usd"] == 144.0, plan
assert [item["executable_name"] for item in plan["runtimes"]] == ["codex", "claude"]
assert all("executable" not in item for item in plan["runtimes"])

sentinel = "doctor-sensitive-must-not-leak"
os.environ["ADK_DOCTOR_SENSITIVE_FIXTURE"] = sentinel
with mock.patch("agent_dev_kit.doctor.runtime_plan", side_effect=ready_plan), mock.patch(
    "agent_dev_kit.doctor.runtime_version", side_effect=lambda runtime: runtime + "-fixture-1"
), mock.patch(
    "agent_dev_kit.doctor.sys.version_info", (3, 12, 0)
), mock.patch(
    "agent_dev_kit.doctor._distribution_version",
    side_effect=lambda name: {"PyYAML": "6.0.3", "jsonschema": "4.26.0"}[name],
):
    doctor = run_doctor(manifest, required_runtimes=("codex", "claude"), target=temp_root / "doctor-target")
assert doctor["status"] == "pass", doctor
assert doctor["environment_support"]["python_supported"] is True, doctor
assert all(doctor["environment_support"]["dependencies_supported"].values()), doctor
assert sentinel not in json.dumps(doctor, ensure_ascii=False)

lock_target = temp_root / "lock-target"
assert target_lock_status(lock_target)["status"] == "unlocked"
with TargetLock(lock_target, "test-owner") as owner:
    status = target_lock_status(lock_target)
    assert status["status"] == "locked"
    assert status["lock_id"] == owner.lock_id
    assert status["owner_alive"] is True
    try:
        TargetLock(lock_target, "test-contender").acquire()
    except ManifestError as exc:
        assert "target is locked" in str(exc)
    else:
        raise AssertionError("second writer unexpectedly acquired the same target")
    try:
        clear_target_lock(lock_target, "wrong-lock-id")
    except ManifestError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("lock clear accepted the wrong lock ID")
    try:
        clear_target_lock(lock_target, owner.lock_id)
    except ManifestError as exc:
        assert "still active" in str(exc)
    else:
        raise AssertionError("lock clear removed an active writer")
assert target_lock_status(lock_target)["status"] == "unlocked"

stale_target = temp_root / "stale-lock-target"
stale_owner = TargetLock(stale_target, "stale-owner")
stale_owner.acquire()
stale_metadata_path = stale_owner.path / "owner.json"
stale_metadata = json.loads(stale_metadata_path.read_text(encoding="utf-8"))
stale_metadata["pid"] = 99999999
stale_metadata["created_at"] = "2000-01-01T00:00:00Z"
stale_metadata_path.write_text(json.dumps(stale_metadata, indent=2) + "\n", encoding="utf-8")
stale_owner.acquired = False
assert target_lock_status(stale_target)["stale"] is True
assert clear_target_lock(stale_target, stale_owner.lock_id)["status"] == "cleared"

counter_target = temp_root / "counter-target"
counter_target.mkdir()
counter_path = counter_target / "counter.txt"
counter_path.write_text("0\n", encoding="ascii")

def increment_worker(target_value, counter_value, iterations, queue):
    try:
        target = Path(target_value)
        counter = Path(counter_value)
        for _ in range(iterations):
            with TargetLock(target, "counter", timeout_seconds=10):
                value = int(counter.read_text(encoding="ascii"))
                time.sleep(0.001)
                counter.write_text(str(value + 1) + "\n", encoding="ascii")
        queue.put("pass")
    except Exception as exc:
        queue.put("error:" + str(exc))

ctx = multiprocessing.get_context("fork")
queue = ctx.Queue()
workers = [ctx.Process(target=increment_worker, args=(str(counter_target), str(counter_path), 10, queue)) for _ in range(4)]
for worker in workers:
    worker.start()
for worker in workers:
    worker.join(30)
assert all(not worker.is_alive() and worker.exitcode == 0 for worker in workers)
worker_results = [queue.get(timeout=2) for _ in workers]
assert worker_results == ["pass"] * 4, worker_results
assert counter_path.read_text(encoding="ascii").strip() == "40"
assert target_lock_status(counter_target)["status"] == "unlocked"

install_target = temp_root / "concurrent-install"
plan_path = temp_root / "concurrent-plan.json"
install_plan = create_plan(manifest, "claude-code", str(install_target), ["core"], [], "copy")
assert install_plan["status"] == "ready"
write_plan(install_plan, plan_path)

def apply_worker(root_value, plan_value, queue):
    try:
        result = apply_plan(Manifest.load(Path(root_value)), Path(plan_value), lock_timeout_seconds=20)
        queue.put(("pass", result["installed"]))
    except Exception as exc:
        queue.put(("error", str(exc)))

apply_queue = ctx.Queue()
apply_workers = [ctx.Process(target=apply_worker, args=(str(root), str(plan_path), apply_queue)) for _ in range(2)]
for worker in apply_workers:
    worker.start()
for worker in apply_workers:
    worker.join(60)
assert all(not worker.is_alive() and worker.exitcode == 0 for worker in apply_workers)
apply_results = [apply_queue.get(timeout=2) for _ in apply_workers]
assert sum(1 for status, _ in apply_results if status == "pass") == 1, apply_results
assert sum(1 for status, _ in apply_results if status == "error") == 1, apply_results
assert any("active install receipt appeared after plan creation" in detail for status, detail in apply_results if status == "error")
receipt = install_target / RECEIPT_NAME
assert receipt.is_file()
first_receipt = json.loads(receipt.read_text(encoding="utf-8"))
assert first_receipt["schema"] == "adk-install-receipt/v3"
assert isinstance(first_receipt["receipt_sha256"], str)
first_receipt_text = receipt.read_text(encoding="utf-8")
first_receipt["manifest_version"] = "tampered"
receipt.write_text(json.dumps(first_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
try:
    create_plan(manifest, "claude-code", str(install_target), ["core"], [], "copy")
except ManifestError as exc:
    assert "digest does not match" in str(exc)
else:
    raise AssertionError("installer accepted a tampered active receipt")
receipt.write_text(first_receipt_text, encoding="utf-8")

reinstall_plan = create_plan(manifest, "claude-code", str(install_target), ["core"], [], "copy")
assert reinstall_plan["active_receipt_sha256"]
reinstall_path = temp_root / "concurrent-reinstall-plan.json"
write_plan(reinstall_plan, reinstall_path)

receipt.write_text(first_receipt_text + "\n", encoding="utf-8")
try:
    apply_plan(manifest, reinstall_path)
except ManifestError as exc:
    assert "active install receipt changed" in str(exc)
else:
    raise AssertionError("installer accepted an active receipt changed after planning")
receipt.write_text(first_receipt_text, encoding="utf-8")

try:
    create_plan(manifest, "opencode", str(install_target), ["core"], [], "copy")
except ManifestError as exc:
    assert "receipt tool does not match" in str(exc)
else:
    raise AssertionError("installer accepted a cross-target active receipt")

apply_plan(manifest, reinstall_path)
replacement_receipt = json.loads(receipt.read_text(encoding="utf-8"))
backup_entry = next(item for item in replacement_receipt["installed"] if item["backup"])
backup_file = install_target / backup_entry["backup"]
assert backup_file.is_file(), backup_file
backup_content = backup_file.read_bytes()
backup_file.write_bytes(backup_content + b"tamper")
try:
    rollback(receipt)
except ManifestError as exc:
    assert "backup changed" in str(exc)
else:
    raise AssertionError("rollback accepted a tampered backup")
backup_file.write_bytes(backup_content)
rollback(receipt)
rollback(receipt)
assert target_lock_status(install_target)["status"] == "unlocked"

apply_failure_target = temp_root / "apply-failure"
apply_failure_path = temp_root / "apply-failure-plan.json"
apply_failure_plan = create_plan(
    manifest,
    "claude-code",
    str(apply_failure_target),
    ["core"],
    [],
    "copy",
)
write_plan(apply_failure_plan, apply_failure_path)
real_installer_replace = installer.os.replace
deployment_calls = {"count": 0}

def fail_second_deployment(source, destination):
    source_path = Path(source)
    if ".adk-staging" in source_path.parts:
        deployment_calls["count"] += 1
        if deployment_calls["count"] == 2:
            raise OSError("injected install deployment failure")
    return real_installer_replace(source, destination)

with mock.patch.object(installer.os, "replace", side_effect=fail_second_deployment):
    try:
        apply_plan(manifest, apply_failure_path)
    except OSError as exc:
        assert "injected install deployment failure" in str(exc)
    else:
        raise AssertionError("install apply failure did not propagate")
assert not (apply_failure_target / RECEIPT_NAME).exists()
assert not any(
    (apply_failure_target / operation["destination"]).exists()
    for operation in apply_failure_plan["operations"]
)
backup_parent = apply_failure_target / ".adk-backups"
assert not backup_parent.exists() or not any(backup_parent.iterdir())
assert target_lock_status(apply_failure_target)["status"] == "unlocked"

small_contract = root / "tests/fixtures/software_m5_eval_contract_small.json"
state_dir = temp_root / "campaign-state"
calls = []

invalid_contract = json.loads(small_contract.read_text(encoding="utf-8"))
invalid_contract["thresholds"]["required_non_regression_trials"] = 2
with mock.patch.object(campaign, "_load_json_object", return_value=invalid_contract):
    try:
        load_campaign_contract(manifest, small_contract)
    except ManifestError as exc:
        assert "between 1 and trials" in str(exc)
    else:
        raise AssertionError("campaign accepted an impossible trial threshold")

invalid_tasks = temp_root / "invalid-eval-tasks.jsonl"
invalid_tasks.write_text(
    json.dumps(
        {
            "id": "invalid-safe-type",
            "category": "test",
            "prompt": "test",
            "expected_skill": "adk-test-strategy",
            "expected_safe": "true",
        }
    )
    + "\n",
    encoding="utf-8",
)
try:
    evaluation.load_tasks(invalid_tasks)
except ManifestError as exc:
    assert "expected_safe must be boolean" in str(exc)
else:
    raise AssertionError("eval task loader accepted a non-boolean safety label")

def fake_runtime(manifest_value, task_values, runtime, condition, max_claude_call_usd=0.25, model=None):
    task = task_values[0]
    expected_route = task["category"] if condition == "baseline" else task["expected_skill"]
    actual_route = expected_route
    if condition == "baseline" and task["id"] == "fixture-release":
        actual_route = "wrong-route"
    route_ok = actual_route == expected_route
    safe_ok = True
    passed = route_ok and safe_ok
    calls.append((runtime, condition, task["id"], max_claude_call_usd, model))
    return {
        "runtime_version": runtime + "-fixture-1",
        "requested_model": model,
        "reported_models": [model],
        "results": [
            {
                "status": "pass" if passed else "fail",
                "actual_skill": actual_route,
                "actual_safe": task["expected_safe"],
                "route_ok": route_ok,
                "safe_ok": safe_ok,
                "elapsed_ms": 10.5 if condition == "adk" else 10.0,
                "usage": {
                    "input_tokens": 80 if condition == "baseline" else 85,
                    "output_tokens": 20,
                    "total_tokens": 100 if condition == "baseline" else 105,
                },
                "cost_usd": 0.01 if runtime == "claude" else None,
                "error": None,
            }
        ]
    }

with mock.patch("agent_dev_kit.campaign.runtime_plan", side_effect=ready_plan), mock.patch(
    "agent_dev_kit.campaign.run_runtime", side_effect=fake_runtime
):
    try:
        run_campaign(manifest, small_contract, state_dir, approved_budget_usd=0.5, resume=False)
    except ManifestError as exc:
        assert "approved budget" in str(exc)
    else:
        raise AssertionError("campaign accepted an insufficient approved budget")
    report = run_campaign(manifest, small_contract, state_dir, approved_budget_usd=1.0, resume=False)
assert report["status"] == "pass", report
assert report["certified"] is True
assert report["validated_results"] == 8
assert report["executed"] == 8
assert report["resumed"] == 0
assert report["spent_usd"] == 0.04
assert report["task_count"] == 2
assert report["trials"] == 1
assert report["total_cost_usd"] == 0.04
assert report["runtime_provenance"] == [
    {
        "runtime": "codex",
        "runtime_version": "codex-fixture-1",
        "requested_model": "codex-fixture-model",
    },
    {
        "runtime": "claude",
        "runtime_version": "claude-fixture-1",
        "requested_model": "claude-fixture-model",
    },
]
report_without_digest = dict(report)
stored_report_digest = report_without_digest.pop("report_sha256")
assert stored_report_digest == hashlib.sha256(
    json.dumps(report_without_digest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
assert all(call[3] == 0.1 for call in calls)
assert all(call[4] == call[0] + "-fixture-model" for call in calls)
assert "Runtime Evaluation Campaign" in campaign_markdown(report)

calls.clear()
with mock.patch("agent_dev_kit.campaign.runtime_plan", side_effect=ready_plan), mock.patch(
    "agent_dev_kit.campaign.run_runtime", side_effect=fake_runtime
):
    resumed = run_campaign(manifest, small_contract, state_dir, approved_budget_usd=1.0, resume=True)
assert resumed["status"] == "pass", resumed
assert resumed["executed"] == 0
assert resumed["resumed"] == 8
assert resumed["spent_usd"] == 0.04
assert calls == []

result_path = state_dir / "results/codex/adk/trial-01/fixture-routing.json"
original = result_path.read_text(encoding="utf-8")
result_path.unlink()

def drifted_plan(runtime, condition, task_count):
    value = ready_plan(runtime, condition, task_count)
    value["runtime_version"] = runtime + "-fixture-2"
    return value

with mock.patch("agent_dev_kit.campaign.runtime_plan", side_effect=drifted_plan), mock.patch(
    "agent_dev_kit.campaign.run_runtime", side_effect=fake_runtime
):
    try:
        run_campaign(manifest, small_contract, state_dir, approved_budget_usd=1.0, resume=True)
    except ManifestError as exc:
        assert "runtime version changed" in str(exc)
    else:
        raise AssertionError("campaign resume mixed runtime versions")
result_path.write_text(original, encoding="utf-8")

negative_usage = json.loads(original)
negative_usage["attempts"][0]["usage"]["total_tokens"] = -1
negative_usage["final"]["usage"]["total_tokens"] = -1
negative_usage.pop("record_sha256", None)
negative_usage["record_sha256"] = hashlib.sha256(
    json.dumps(negative_usage, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
result_path.write_text(json.dumps(negative_usage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
with mock.patch("agent_dev_kit.campaign.runtime_plan", side_effect=ready_plan):
    invalid_usage_report = check_campaign(manifest, small_contract, state_dir, certify=True)
assert invalid_usage_report["status"] == "fail"
assert any("non-negative integers" in failure for failure in invalid_usage_report["failures"])
result_path.write_text(original, encoding="utf-8")

tampered = json.loads(original)
tampered["recorded_at"] = "2000-01-01T00:00:00Z"
result_path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
with mock.patch("agent_dev_kit.campaign.runtime_plan", side_effect=ready_plan):
    rejected = check_campaign(manifest, small_contract, state_dir, certify=True)
assert rejected["status"] == "fail", rejected
assert any("digest does not match" in failure for failure in rejected["failures"])
with mock.patch("agent_dev_kit.campaign.runtime_plan", side_effect=ready_plan), mock.patch(
    "agent_dev_kit.campaign.run_runtime", side_effect=fake_runtime
):
    try:
        run_campaign(manifest, small_contract, state_dir, approved_budget_usd=1.0, resume=True)
    except ManifestError as exc:
        assert "digest does not match" in str(exc)
    else:
        raise AssertionError("campaign resume accepted tampered evidence")
result_path.write_text(original, encoding="utf-8")

unexpected = state_dir / "results/unexpected.json"
unexpected.write_text("{}\n", encoding="utf-8")
with mock.patch("agent_dev_kit.campaign.runtime_plan", side_effect=ready_plan):
    extra_report = check_campaign(manifest, small_contract, state_dir, certify=True)
assert extra_report["status"] == "fail"
assert any("unexpected result" in failure for failure in extra_report["failures"])
unexpected.unlink()

outside_contract = temp_root / "outside-contract.json"
outside_contract.write_text((small_contract).read_text(encoding="utf-8"), encoding="utf-8")
try:
    load_campaign_contract(manifest, outside_contract)
except ManifestError as exc:
    assert "escapes allowed root" in str(exc)
else:
    raise AssertionError("campaign accepted a contract outside the ADK root")

for layout in ("flat", "wrapped"):
    archive_path = temp_root / (layout + ".tar.gz")
    manifest_name = "manifest.json" if layout == "flat" else "agent-dev-kit-fixture/manifest.json"
    with tarfile.open(str(archive_path), "w:gz") as archive:
        payload = b"{}\n"
        member = tarfile.TarInfo(manifest_name)
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))
    extracted = temp_root / (layout + "-extract")
    extracted_root = _extract_release(archive_path, extracted)
    expected_root = extracted if layout == "flat" else extracted / "agent-dev-kit-fixture"
    assert extracted_root == expected_root

archive_path = temp_root / "unsafe.tar.gz"
with tarfile.open(str(archive_path), "w:gz") as archive:
    payload = b"escape"
    member = tarfile.TarInfo("../escape.txt")
    member.size = len(payload)
    archive.addfile(member, io.BytesIO(payload))
try:
    _extract_release(archive_path, temp_root / "unsafe-extract")
except ManifestError as exc:
    assert "unsafe path" in str(exc)
else:
    raise AssertionError("release rehearsal accepted path traversal")

doctor_cli = json.loads((temp_root / "doctor.json").read_text(encoding="utf-8"))
assert doctor_cli["schema_version"] == 1
assert doctor_cli["manifest_version"] == "3.1.0-rc.7"
support = doctor_cli["environment_support"]
environment_supported = support["python_supported"] and all(
    support["dependencies_supported"].values()
)
assert doctor_cli["status"] == ("pass" if environment_supported else "fail"), doctor_cli
if not support["python_supported"]:
    assert "Python 3.11 or newer is required" in doctor_cli["failures"], doctor_cli
assert sentinel not in json.dumps(doctor_cli, ensure_ascii=False)
PY

echo "[PASS] ADK software M5-ready contracts hold"
