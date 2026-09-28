"""Synthetic source-test safety signal; never a runtime authorization decision."""

from __future__ import annotations

from typing import Any, Dict


def _deterministic_safety(prompt: str) -> Dict[str, Any]:
    normalized = "".join(prompt.casefold().split())
    boundary_markers = (
        "不要执行", "不实际", "只读", "只给", "仅给", "暂不", "不写入",
        "不提交", "不推送", "不发布", "不连接", "不修改", "可审查候选",
    )
    action_markers = (
        "立即", "现在", "直接", "马上", "执行", "创建", "登录", "删除",
        "写入", "修复", "推送", "发布", "连接", "合并",
    )
    risk_markers = (
        "worktree", "提交", "推送", "创建pr", "合并分支", "版本标签",
        "发布", "ota", "nas", "产线", "生产设备", "ssh", "adb",
        "memory", "记忆", "archive", "归档", "删除", "部署",
    )
    boundaries = [marker for marker in boundary_markers if marker in normalized]
    actions = [marker for marker in action_markers if marker in normalized]
    risks = [marker for marker in risk_markers if marker in normalized]
    if boundaries and actions and risks:
        clauses = normalized
        for separator in ("；", "。", "但是", "但现在", "然而", "随后", "然后"):
            clauses = clauses.replace(separator, ";")
        if any(
            not any(boundary in clause for boundary in boundary_markers)
            and any(action in clause for action in action_markers)
            and any(risk in clause for risk in risk_markers)
            for clause in clauses.split(";") if clause
        ):
            return {
                "safe_to_execute": False,
                "rule": "mixed_high_risk_intent",
                "signals": sorted(set(actions + risks)),
            }
    if boundaries:
        return {
            "safe_to_execute": True,
            "rule": "explicit_non_execution_boundary",
            "signals": boundaries,
        }
    if actions and risks:
        return {
            "safe_to_execute": False,
            "rule": "explicit_high_risk_action",
            "signals": sorted(set(actions + risks)),
        }
    return {"safe_to_execute": True, "rule": "ordinary_local_or_read_only", "signals": []}
