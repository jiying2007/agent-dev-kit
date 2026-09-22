"""Deterministic source/test-layer effect evaluation."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping

from .evaluation_runtime import _deterministic_safety, _load_effect_inputs, _prompt_digest
from .matcher import match_text
from .model import Manifest, ManifestError, ensure_within, sha256_file

EFFECT_CONTRACT_SCHEMA = "adk-effect-eval-contract/v1"
EFFECT_LABEL_SCHEMA = "adk-effect-eval-labels/v1"
EFFECT_THRESHOLD_NAMES = (
    "route_accuracy",
    "safety_accuracy",
    "trace_accuracy",
    "outcome_accuracy",
    "minimum_ablation_delta",
)


def run_effect_eval(manifest: Manifest, contract_path: Path) -> Dict[str, Any]:
    contract_path = ensure_within(contract_path.resolve(), manifest.root, "effect eval contract")
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("effect eval contract is invalid") from exc
    if not isinstance(contract, dict) or contract.get("schema") != EFFECT_CONTRACT_SCHEMA:
        raise ManifestError("unsupported effect eval contract schema")
    if contract.get("evidence_layer") != "source-test":
        raise ManifestError("effect eval evidence_layer must be source-test")
    ablation_contract = contract.get("ablation")
    if (
        not isinstance(ablation_contract, dict)
        or ablation_contract.get("component") != "routing.intents"
        or not isinstance(ablation_contract.get("method"), str)
        or not ablation_contract["method"].strip()
    ):
        raise ManifestError("effect eval ablation contract is invalid")
    limitations = contract.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise ManifestError("effect eval limitations must be a non-empty string array")
    dataset = contract.get("dataset")
    if not isinstance(dataset, dict):
        raise ManifestError("effect eval dataset contract is missing")
    inputs_path = ensure_within(manifest.root / str(dataset.get("inputs", "")), manifest.root, "effect inputs")
    labels_path = ensure_within(manifest.root / str(dataset.get("labels", "")), manifest.root, "effect labels")
    for path, key in ((inputs_path, "inputs_sha256"), (labels_path, "labels_sha256")):
        expected_digest = dataset.get(key)
        if not isinstance(expected_digest, str) or sha256_file(path) != expected_digest:
            raise ManifestError("effect eval {} does not match contract digest".format(key))
    inputs = _load_effect_inputs(inputs_path)
    try:
        label_document = json.loads(labels_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("effect eval labels are invalid") from exc
    if not isinstance(label_document, dict) or label_document.get("schema") != EFFECT_LABEL_SCHEMA:
        raise ManifestError("unsupported effect eval label schema")
    raw_labels = label_document.get("labels")
    if not isinstance(raw_labels, list):
        raise ManifestError("effect eval labels must be an array")
    labels: Dict[str, Mapping[str, Any]] = {}
    for label in raw_labels:
        if not isinstance(label, dict) or set(label) != {"id", "expected_skill", "expected_safe", "expected_outcome"}:
            raise ManifestError("effect eval label fields are invalid")
        if not isinstance(label["id"], str) or label["id"] in labels:
            raise ManifestError("effect eval label IDs must be unique strings")
        if not isinstance(label["expected_skill"], str) or not isinstance(label["expected_safe"], bool):
            raise ManifestError("effect eval labels have invalid expected values")
        if label["expected_outcome"] != "route-and-safety":
            raise ManifestError("effect eval expected_outcome must be route-and-safety")
        labels[label["id"]] = label
    input_ids = {item["id"] for item in inputs}
    if input_ids != set(labels):
        raise ManifestError("effect eval inputs and labels do not have identical IDs")
    minimum_cases = contract.get("minimum_cases")
    if isinstance(minimum_cases, bool) or not isinstance(minimum_cases, int) or len(inputs) < minimum_cases:
        raise ManifestError("effect eval dataset is below minimum_cases")
    required_splits = contract.get("required_splits")
    split_counts = {name: sum(1 for item in inputs if item["split"] == name) for name in ("ood", "adversarial")}
    if (
        not isinstance(required_splits, dict)
        or set(required_splits) != set(split_counts)
        or any(
            isinstance(required_splits[name], bool)
            or not isinstance(required_splits[name], int)
            or required_splits[name] < 1
            for name in split_counts
        )
        or any(
            split_counts[name] < required_splits.get(name, 0) for name in split_counts
        )
    ):
        raise ManifestError("effect eval dataset is below required split counts")
    thresholds = contract.get("thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) != set(EFFECT_THRESHOLD_NAMES) or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or value > 1
        for value in thresholds.values()
    ):
        raise ManifestError("effect eval thresholds are invalid")
    allowed_sources = contract.get("allowed_trace_sources")
    if not isinstance(allowed_sources, list) or not allowed_sources:
        raise ManifestError("effect eval allowed_trace_sources are missing")
    managed_skills = {
        str(item.get("name"))
        for item in manifest.data.get("skills", []) + manifest.data.get("optional_skills", [])
        if isinstance(item, dict) and item.get("name")
    }

    ablated_data = copy.deepcopy(manifest.data)
    if isinstance(ablated_data.get("routing"), dict):
        ablated_data["routing"]["enabled"] = False
    ablated_manifest = Manifest(manifest.root, ablated_data, manifest.source)
    results: List[Dict[str, Any]] = []
    ablated_passed = 0
    for item in inputs:
        label = labels[item["id"]]
        matched = match_text(manifest, item["prompt"])
        actual_skill = str(matched.get("skill")) if matched.get("match") is True else None
        safety = _deterministic_safety(item["prompt"])
        route_ok = actual_skill == label["expected_skill"]
        safety_ok = safety["safe_to_execute"] == label["expected_safe"]
        trace_assertions = {
            "route_selected": matched.get("match") is True,
            "managed_skill": actual_skill in managed_skills,
            "allowed_source": matched.get("source") in allowed_sources,
            "safety_rule_recorded": bool(safety.get("rule")),
        }
        trace_ok = all(trace_assertions.values())
        ablated = match_text(ablated_manifest, item["prompt"])
        ablated_skill = str(ablated.get("skill")) if ablated.get("match") is True else None
        ablated_route_ok = ablated_skill == label["expected_skill"]
        ablated_passed += int(ablated_route_ok)
        results.append(
            {
                "id": item["id"],
                "split": item["split"],
                "category": item["category"],
                "prompt_sha256": _prompt_digest(item["prompt"]),
                "expected_skill": label["expected_skill"],
                "actual_skill": actual_skill,
                "route_ok": route_ok,
                "expected_safe": label["expected_safe"],
                "actual_safe": safety["safe_to_execute"],
                "safety_ok": safety_ok,
                "trace": {
                    "source": matched.get("source"),
                    "supporting_skills": matched.get("supporting_skills", []),
                    "safety_rule": safety["rule"],
                    "safety_signal_count": len(safety["signals"]),
                    "assertions": trace_assertions,
                },
                "trace_ok": trace_ok,
                "outcome_ok": route_ok and safety_ok,
                "ablation": {"routing_disabled_route_ok": ablated_route_ok},
            }
        )

    total = len(results)
    route_accuracy = sum(int(item["route_ok"]) for item in results) / total
    safety_accuracy = sum(int(item["safety_ok"]) for item in results) / total
    trace_accuracy = sum(int(item["trace_ok"]) for item in results) / total
    outcome_accuracy = sum(int(item["outcome_ok"]) for item in results) / total
    ablated_accuracy = ablated_passed / total
    ablation_delta = route_accuracy - ablated_accuracy
    metrics = {
        "route_accuracy": round(route_accuracy, 4),
        "safety_accuracy": round(safety_accuracy, 4),
        "trace_accuracy": round(trace_accuracy, 4),
        "outcome_accuracy": round(outcome_accuracy, 4),
        "minimum_ablation_delta": round(ablation_delta, 4),
    }
    gate = {name: metrics[name] >= float(thresholds[name]) for name in EFFECT_THRESHOLD_NAMES}
    split_metrics: Dict[str, Any] = {}
    for split in ("ood", "adversarial"):
        selected = [item for item in results if item["split"] == split]
        split_metrics[split] = {
            "total": len(selected),
            "route_accuracy": round(sum(int(item["route_ok"]) for item in selected) / len(selected), 4),
            "safety_accuracy": round(sum(int(item["safety_ok"]) for item in selected) / len(selected), 4),
            "outcome_accuracy": round(sum(int(item["outcome_ok"]) for item in selected) / len(selected), 4),
        }
    return {
        "schema": "adk-effect-eval-report/v1",
        "status": "pass" if all(gate.values()) else "fail",
        "evidence_layer": "source-test",
        "dataset": {
            "inputs": inputs_path.relative_to(manifest.root).as_posix(),
            "labels": labels_path.relative_to(manifest.root).as_posix(),
            "inputs_sha256": dataset["inputs_sha256"],
            "labels_sha256": dataset["labels_sha256"],
            "label_visibility": dataset.get("label_visibility"),
            "total": total,
            "split_counts": split_counts,
        },
        "thresholds": thresholds,
        "metrics": metrics,
        "split_metrics": split_metrics,
        "ablation": {
            "component": "routing.intents",
            "candidate_route_accuracy": round(route_accuracy, 4),
            "routing_disabled_route_accuracy": round(ablated_accuracy, 4),
            "delta": round(route_accuracy - ablated_accuracy, 4),
        },
        "quality_gate": gate,
        "limitations": limitations,
        "results": results,
    }
