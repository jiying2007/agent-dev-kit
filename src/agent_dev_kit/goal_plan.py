"""Read-only Goal contract lint/render; never a runtime authority or evidence verifier."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Optional, Sequence

from .planning_state import _reject_symlink_path, valid_work_in_progress
from .strict_json import read_bytes as read_bounded_bytes, loads as load_strict_json


MAX_PLAN_BYTES = 65536
MAX_STATE_BYTES = 8192


def _load_document(path: Path, limit: int) -> tuple[dict, bytes]:
    _reject_symlink_path(path)
    raw = read_bounded_bytes(path, max_bytes=limit, regular_only=True)
    value = load_strict_json(raw, max_bytes=limit)
    if not isinstance(value, dict):
        raise ValueError("document must be an object")
    return value, raw


def load(path: Path, limit: int) -> dict:
    return _load_document(path, limit)[0]


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _texts(value: Any, minimum: int = 1, maximum: int = 100) -> bool:
    return (isinstance(value, list) and minimum <= len(value) <= maximum
            and all(_text(item) for item in value) and len(set(value)) == len(value))


def check(plan: dict, state: Optional[dict] = None) -> dict:
    reasons = []
    required = {"schema_version", "objective", "original_goal_ref", "constraints",
                "parent_criteria", "deliverables", "batch", "budget_proposal"}
    if set(plan) != required or plan.get("schema_version") != "adk.goal-plan/v1":
        reasons.append("plan-fields-invalid")
    for key in ("objective", "original_goal_ref"):
        if not _text(plan.get(key)):
            reasons.append(key + "-missing")
    if not _texts(plan.get("constraints"), maximum=20):
        reasons.append("constraints-invalid")
    parents = plan.get("parent_criteria")
    if not _texts(parents):
        reasons.append("parent-criteria-invalid")
        parents = []
    items = plan.get("deliverables")
    ids, covered, graph = set(), set(), {}
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        reasons.append("deliverables-invalid")
        items = []
    for item in items:
        fields = {"id", "parents", "outcome", "verify", "evidence", "depends_on", "status", "layer"}
        if not isinstance(item, dict) or set(item) != fields:
            reasons.append("deliverable-fields-invalid")
            continue
        key = item["id"]
        if not _text(key) or key in ids:
            reasons.append("deliverable-id-invalid")
            continue
        ids.add(key)
        if not _texts(item["parents"]) or any(p not in parents for p in item["parents"]):
            reasons.append("parent-reference-invalid")
        else:
            covered.update(item["parents"])
        if not _text(item["outcome"]) or not _texts(item["verify"], maximum=12):
            reasons.append("observable-acceptance-missing")
        if not _texts(item["evidence"], minimum=0, maximum=12):
            reasons.append("evidence-refs-invalid")
        if item["status"] not in ("open", "ready", "blocked", "closed"):
            reasons.append("deliverable-status-invalid")
        if item["status"] == "closed" and not item["evidence"]:
            reasons.append("closed-without-evidence")
        if item["layer"] not in ("software", "board", "external"):
            reasons.append("evidence-layer-invalid")
        if not _texts(item["depends_on"], minimum=0):
            reasons.append("dependencies-invalid")
        else:
            graph[key] = item["depends_on"]
    if set(parents) - covered:
        reasons.append("original-criteria-unmapped")
    if any(dep not in ids for deps in graph.values() for dep in deps):
        reasons.append("unknown-dependency")
    statuses = {x["id"]: x["status"] for x in items
                if isinstance(x, dict) and _text(x.get("id")) and "status" in x}
    for key, deps in graph.items():
        if statuses.get(key) in ("closed", "ready") and any(statuses.get(dep) != "closed" for dep in deps):
            reasons.append("ready-or-closed-with-open-dependency")
    remaining = {key: set(deps) for key, deps in graph.items()}
    while remaining:
        leaves = {key for key, deps in remaining.items() if not deps}
        if not leaves:
            reasons.append("dependency-cycle-or-unresolved")
            break
        remaining = {key: deps - leaves for key, deps in remaining.items() if key not in leaves}
    batch = plan.get("batch")
    fields = {"id", "deliverables", "scope", "done_when", "verification", "stop", "replan_effect"}
    if not isinstance(batch, dict) or set(batch) != fields:
        reasons.append("batch-fields-invalid")
    else:
        selected = batch["deliverables"]
        if not _text(batch["id"]) or not _texts(selected, maximum=4) or any(x not in ids for x in selected):
            reasons.append("batch-selection-invalid")
        elif any(statuses.get(x) not in ("ready", "open") for x in selected):
            reasons.append("batch-selected-unavailable-deliverable")
        elif any(statuses.get(dep) != "closed" for x in selected for dep in graph.get(x, [])):
            reasons.append("batch-selected-with-open-dependency")
        if not _texts(batch["scope"], maximum=20) or not _text(batch["done_when"]):
            reasons.append("batch-exit-or-scope-missing")
        verification = batch["verification"]
        if (not isinstance(verification, dict) or set(verification) != {"targeted", "milestone", "final"}
                or any(not _texts(v, maximum=12) for v in verification.values())):
            reasons.append("verification-scopes-invalid")
        stop = batch["stop"]
        if (not isinstance(stop, dict) or set(stop) != {"same_failure_limit", "nonclosing_batch_limit", "external_trigger"}
                or any(type(stop.get(k)) is not int or stop[k] < 1 for k in ("same_failure_limit", "nonclosing_batch_limit"))
                or not _text(stop.get("external_trigger"))):
            reasons.append("stop-condition-invalid")
        if not _text(batch["replan_effect"]):
            reasons.append("replan-effect-missing")
    budget = plan.get("budget_proposal")
    if (not isinstance(budget, dict) or set(budget) != {"tokens", "basis", "native_goal_applied"}
            or type(budget.get("tokens")) is not int or budget["tokens"] < 1
            or not _text(budget.get("basis")) or budget.get("native_goal_applied") is not False):
        reasons.append("budget-proposal-invalid-or-claims-authority")
    if state is not None:
        required_state = {"schema_version", "goal_ref", "milestone", "evidence_refs", "blockers", "next_actions", "history_refs"}
        if (not required_state <= set(state) or set(state) - required_state - {"work_in_progress"}
                or state.get("schema_version") != "adk.current-state/v1"):
            reasons.append("current-state-fields-invalid")
        if "work_in_progress" in state and not valid_work_in_progress(state["work_in_progress"]):
            reasons.append("current-state-work-in-progress-invalid")
        for key in ("goal_ref", "milestone"):
            if not _text(state.get(key)):
                reasons.append("state-" + key + "-invalid")
        for key, low, high in (("evidence_refs", 0, 8), ("blockers", 0, 8), ("next_actions", 1, 3), ("history_refs", 0, 3)):
            if not _texts(state.get(key), minimum=low, maximum=high):
                reasons.append("state-" + key + "-invalid")
    return {"schema_version": "adk.goal-plan-check/v1", "status": "fail" if reasons else "pass",
            "read_only": True, "runtime_authority": False, "completion_allowed": False,
            "evidence_contents_verified": False, "reasons": sorted(set(reasons)),
            "parent_count": len(parents), "deliverable_count": len(items)}


def render(plan: dict, state: Optional[dict] = None) -> str:
    lines = ["Goal 草案（未启动、未修改既有目标）：", plan["objective"],
             "完整原合同：" + plan["original_goal_ref"],
             "约束：" + "；".join(plan["constraints"]),
             "当前批次：" + plan["batch"]["id"], "退出条件：" + plan["batch"]["done_when"],
             "范围：" + "；".join(plan["batch"]["scope"]),
             "预算提案：{} tokens；未设置原生预算。".format(plan["budget_proposal"]["tokens"]),
             "停止/重排：同因{}次、非关闭批次{}次；{}".format(
                 plan["batch"]["stop"]["same_failure_limit"],
                 plan["batch"]["stop"]["nonclosing_batch_limit"],
                 plan["batch"]["stop"]["external_trigger"]),
             "重规划效果核验：" + plan["batch"]["replan_effect"],
             "阶段仅使用定向/里程碑验证；整体完成才运行 final。",
             "原目标全部验收保留；子项关闭不等于父目标完成，不重建或清零既有 Goal。"]
    if state is not None:
        lines += ["当前：" + state["milestone"], "下一动作：", *state["next_actions"]]
    else:
        wanted = set(plan["batch"]["deliverables"])
        for item in plan["deliverables"]:
            if item["id"] in wanted:
                lines += [item["id"] + "：" + item["outcome"], *item["verify"]]
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "render", "resume"))
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--state", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "resume" and args.state is None:
            raise ValueError("resume requires --state")
        plan, plan_raw = _load_document(args.plan, MAX_PLAN_BYTES)
        state = load(args.state, MAX_STATE_BYTES) if args.state else None
        result = check(plan, state)
        result["plan_sha256"] = hashlib.sha256(plan_raw).hexdigest()
        if args.action == "check" or result["status"] == "fail":
            print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        else:
            output = render(plan, state)
            if len(output.encode("utf-8")) > MAX_STATE_BYTES:
                raise ValueError("rendered frontier exceeds byte limit; shorten current batch without dropping original criteria")
            print(output)
        return 1 if result["status"] == "fail" else 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"status": "fail", "read_only": True, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
