"""Deterministic task-cost classification and bounded execution receipts."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Sequence


TASK_TYPES = {"implementation", "debug", "decision", "release", "validation", "general"}
RISK_LEVELS = {"low", "medium", "high"}

POLICIES: Dict[str, Dict[str, Any]] = {
    "micro": {
        "primary_skill_budget": 0,
        "supporting_skill_budget": 0,
        "hub_preflight": "skip",
        "context_budget": "small",
        "read_tier": "L0",
        "verification_tier": "targeted",
        "archive_candidate": "no",
        "raw_required": False,
    },
    "standard": {
        "primary_skill_budget": 1,
        "supporting_skill_budget": 0,
        "hub_preflight": "conditional",
        "context_budget": "small",
        "read_tier": "L1",
        "verification_tier": "targeted",
        "archive_candidate": "conditional",
        "raw_required": False,
    },
    "complex": {
        "primary_skill_budget": 1,
        "supporting_skill_budget": 1,
        "hub_preflight": "required",
        "context_budget": "small",
        "read_tier": "L1",
        "verification_tier": "regression",
        "archive_candidate": "conditional",
        "raw_required": False,
    },
    "high-risk": {
        "primary_skill_budget": 1,
        "supporting_skill_budget": 1,
        "hub_preflight": "required",
        "context_budget": "normal",
        "read_tier": "L2",
        "verification_tier": "full-gate",
        "archive_candidate": "required",
        "raw_required": True,
    },
}


def classify_task_cost(
    task: str,
    *,
    task_type: str = "general",
    risk_level: str = "low",
    changed_files: int = 0,
    project_facts: bool = False,
    long_task: bool = False,
    shared_contract: bool = False,
    external_write: bool = False,
    destructive: bool = False,
) -> Dict[str, Any]:
    if not task.strip():
        raise ValueError("task must not be empty")
    if task_type not in TASK_TYPES:
        raise ValueError("unsupported task type: {}".format(task_type))
    if risk_level not in RISK_LEVELS:
        raise ValueError("unsupported risk level: {}".format(risk_level))
    if changed_files < 0:
        raise ValueError("changed_files must be >= 0")

    reasons = []  # type: list[str]
    if destructive:
        reasons.append("destructive-action")
    if external_write:
        reasons.append("external-write")
    if task_type == "release":
        reasons.append("release-task")
    if risk_level == "high":
        reasons.append("explicit-high-risk")

    if reasons:
        task_cost = "high-risk"
    elif risk_level == "medium" or long_task or shared_contract or changed_files >= 4 or task_type == "decision":
        task_cost = "complex"
        if risk_level == "medium":
            reasons.append("explicit-medium-risk")
        if long_task:
            reasons.append("long-task")
        if shared_contract:
            reasons.append("shared-contract")
        if changed_files >= 4:
            reasons.append("multi-file-change")
        if task_type == "decision":
            reasons.append("decision-task")
    elif project_facts or task_type in {"debug", "validation"} or changed_files >= 2:
        task_cost = "standard"
        if project_facts:
            reasons.append("project-facts")
        if task_type in {"debug", "validation"}:
            reasons.append("evidence-task")
        if changed_files >= 2:
            reasons.append("multi-file-local-change")
    else:
        task_cost = "micro"
        reasons.append("bounded-local-task")

    signals = {
        "task_type": task_type,
        "risk_level": risk_level,
        "changed_files": changed_files,
        "project_facts": project_facts,
        "long_task": long_task,
        "shared_contract": shared_contract,
        "external_write": external_write,
        "destructive": destructive,
    }
    return {
        "schema_version": 1,
        "receipt_type": "adk-task-cost",
        "status": "pass",
        "task_sha256": hashlib.sha256(task.encode("utf-8")).hexdigest(),
        "source_text_stored": False,
        "task_cost": task_cost,
        "classification_reasons": reasons,
        "signals": signals,
        "execution_budget": dict(POLICIES[task_cost]),
    }


def validate_skill_usage(receipt: Dict[str, Any], skills: Sequence[str]) -> Dict[str, Any]:
    unique_skills = sorted(set(value for value in skills if value))
    budget = int((receipt.get("execution_budget") or {}).get("primary_skill_budget", 0)) + int(
        (receipt.get("execution_budget") or {}).get("supporting_skill_budget", 0)
    )
    return {
        "status": "pass" if len(unique_skills) <= budget else "fail",
        "skill_count": len(unique_skills),
        "skill_budget": budget,
        "skills": unique_skills,
    }
