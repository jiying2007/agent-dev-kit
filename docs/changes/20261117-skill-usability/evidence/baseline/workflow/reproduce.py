"""Read-only source audit; generated evidence stays outside the repository.

This is deterministic contract/export evidence, never a model/runtime benchmark.
Invoke through the workspace RTK wrapper with PYTHONDONTWRITEBYTECODE=1.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import yaml


ROOT = Path("/workspace/scratch/fe8de3b42084/adk-skill-usability")
OUT = Path(__file__).resolve().parent
EXPECTED_HEAD = "78c3be7f6f9b5ee2e557de54156532fb3169198d"
sys.path.insert(0, str(ROOT / "src"))

from agent_dev_kit.compiler import export_assets
from agent_dev_kit.intent_boundary import TASK_PACKAGE_SCHEMA, validate_task_package
from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest


def save(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "--no-pager", "--no-optional-locks", "-c", "core.fsmonitor=false", *args],
        cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()


def routing(manifest: Manifest) -> list[dict[str, object]]:
    cases = [
        ("review-chinese-general", "请帮我做代码评审", "adk-code-review-loop"),
        ("review-chinese-feedback", "请核实这条代码评审意见，不修改代码", "adk-code-review-loop"),
        ("review-control", "请进行独立代码审查", "adk-code-review-loop"),
        ("commit-control", "请校验 commit message", "adk-commit-pr-quality-gate"),
        ("python-diagnosis", "诊断这个 Python 脚本的异常", "adk-systematic-debugging"),
        ("web-diagnosis", "先诊断 Web API 超时的根因", "adk-systematic-debugging"),
        ("database-rollback", "请检查数据库回滚方案", None),
        ("device-state-design", "帮我设计设备状态机，不涉及量产或OTA", None),
        ("field-positive", "检查嵌入式量产产测和现场维护 readiness", "adk-production-field-readiness"),
        ("debug-positive", "请定位根因并保留最小复现", "adk-systematic-debugging"),
        ("handoff-natural", "请为跨团队交接生成一页说明", "adk-cross-team-handoff"),
        ("adr-operation", "请写 ADR，记录我们已经接受的 API 接口兼容方案", "adk-adr-writer"),
        ("approved-implementation", "按已批准验收实现新功能，不要重新访谈", None),
        ("generic-test-writing", "给这个 Python 函数补测试并运行", None),
    ]
    observed = []
    for case_id, prompt, expected in cases:
        result = match_text(manifest, prompt, scope="auto")
        observed.append({
            "id": case_id, "prompt": prompt,
            "expected_primary_if_defined": expected,
            "observed": result,
            "expectation_met": result.get("skill") == expected if expected else None,
            "evidence_layer": "deterministic-source-matcher",
        })
    save("routing.json", observed)
    return observed


def task_contract() -> dict[str, object]:
    # Ordinary read-only research handoff. Every value is synthetic fixture data.
    control = {
        "structured_output_schema": TASK_PACKAGE_SCHEMA,
        "strict_schema_decision": True,
        "refusal_handling": "blocked or replan",
        "goal": "Review the timeout boundary",
        "context": "A frozen source snapshot and already authorized read scope",
        "constraints": ["read-only", "scope_read: src/retry.py", "scope_write: []"],
        "done_when": ["The boundary result has a source and test citation"],
        "primary_action": "research",
        "action_mode": "read-only",
        "verification": ["Inspect the timeout boundary fixture"],
        "artifacts": ["timeout-review.md"],
        "blockers": ["Source unavailable"],
        "work_item_kind": "research",
        "question_to_resolve": "Is elapsed_ms == deadline_ms allowed?",
        "evidence_required": ["Current condition and its boundary test"],
        "implementation_permission": "forbidden",
        "exit_gate": "evidence-reviewed",
        "handoff_target": "task-owner",
        "retention_decision": "keep-final",
    }
    instruction_fields = {
        "global_constraints": ["read-only"],
        "interfaces": ["timeout boundary"],
        "scope_read": ["src/retry.py"],
        "scope_write": [],
        "ready_to_handoff": True,
    }
    variants = {
        "canonical_control": control,
        "with_published_machine_fields": {**control, **instruction_fields},
        "forbidden_write_control": {**control, "implementation_permission": "approved"},
    }
    result = {
        "schema": TASK_PACKAGE_SCHEMA,
        "published_instruction": "skills/adk-task-breakdown/references/task-packaging.md:7",
        "consumer": "src/agent_dev_kit/intent_boundary.py:validate_task_package",
        "cases": [{"id": name, "payload": value,
                   "errors": list(validate_task_package(value))}
                  for name, value in variants.items()],
        "evidence_layer": "actual-production-validator-invocation",
        "model_behavior": "not-measured",
    }
    malformed = []
    for case_id, delta in (
        ("bad-artifact-element", {"artifacts": [1]}),
        ("bad-artifacts-container", {"artifacts": None}),
        ("bad-kind-container", {"work_item_kind": []}),
        ("bad-retention-container", {"retention_decision": []}),
    ):
        try:
            errors = list(validate_task_package({**control, **delta}))
            observed = {"id": case_id, "delta": delta, "errors": errors, "exception": None}
        except Exception as exc:
            observed = {"id": case_id, "delta": delta, "errors": None,
                        "exception": {"type": type(exc).__name__, "message": str(exc)}}
        malformed.append(observed)
    save("task-package-validator.json", result)
    save("task-package-malformed.json", malformed)
    return result


def exported(manifest: Manifest, entries: list[dict[str, str]]) -> list[dict[str, object]]:
    results = []
    profiles = ["core", "team-core", "research-intake", "large-refactor", "personal-core"]
    for target in ("claude-code", "opencode"):
        # Only this script's disposable consumer exports are replaced on replay.
        exported_result = export_assets(manifest, target, OUT / "exports", profiles, clean=True)
        consumer = Path(exported_result["output"])
        rows = []
        for entry in entries:
            found = [p for p in consumer.rglob("SKILL.md") if p.parent.name == entry["name"]]
            if len(found) != 1:
                raise AssertionError((target, entry["name"], found))
            source = ROOT / entry["path"]
            skill = found[0]
            support = []
            for reference in sorted(source.parent.rglob("*")):
                if not reference.is_file() or reference.name == "SKILL.md":
                    continue
                relative = reference.relative_to(source.parent)
                package_ref = skill.parent / relative
                support.append({"path": relative.as_posix(), "exists": package_ref.is_file(),
                                "bytes_equal": package_ref.is_file()
                                and reference.read_bytes() == package_ref.read_bytes()})
            rows.append({"name": entry["name"], "source": entry["path"],
                         "exported_skill": str(skill), "support_files": support})
        names = [p.relative_to(consumer).as_posix() for p in consumer.rglob("*") if p.is_file()]
        definitions = []
        for path in consumer.rglob("*"):
            if path.is_file() and path.suffix in {".json", ".py", ".md", ".yaml"}:
                text = path.read_text()
                if "adk-task-package-schema-v2" in text:
                    definitions.append({"path": path.relative_to(consumer).as_posix(),
                                        "mentions": text.count("adk-task-package-schema-v2")})
        results.append({"target": target, "status": exported_result["status"],
                        "output": str(consumer), "profiles": profiles,
                        "workflow_skills": rows, "v2_mentions": definitions,
                        "source_contract_files_present": {
                            p: p in names for p in (
                                "manifests/structured_output_contracts.json",
                                "src/agent_dev_kit/intent_boundary.py",
                                "templates/artifacts/task-breakdown-template.md",
                                "templates/governance/codify-decision.md",
                            )},
                        "all_file_paths": names})
    save("exports.json", results)
    return results


def main() -> None:
    if git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise SystemExit("Source identity changed; refusing stale baseline audit")
    initial_status = git("status", "--porcelain=v1", "--untracked-files=all")
    manifest = Manifest.load(ROOT)
    entries = json.loads((OUT.parent / "groups.json").read_text())["groups"]["workflow"]
    inventory = []
    for entry in entries:
        path = ROOT / entry["path"]
        metadata = yaml.safe_load(path.read_text().split("---", 2)[1])
        positive = metadata["triggers"][0]
        negative = metadata["non_triggers"][0]
        inventory.append({**entry, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "line_count": len(path.read_text().splitlines()),
                          "byte_count": path.stat().st_size,
                          "isolated_positive": {"prompt": positive,
                              "result": match_text(manifest, positive, skill=entry["name"], scope="skill")},
                          "isolated_negative": {"prompt": negative,
                              "result": match_text(manifest, negative, skill=entry["name"], scope="skill")},
                          "support_read": [str(p.relative_to(ROOT)) for p in sorted(path.parent.rglob("*.md"))
                                           if p.name != "SKILL.md"]})
    save("source-inventory.json", inventory)
    routes = routing(manifest)
    contract = task_contract()
    exports = exported(manifest, entries)
    final_status = git("status", "--porcelain=v1", "--untracked-files=all")
    identity = {"head": EXPECTED_HEAD, "version": manifest.version,
                "initial_status": initial_status, "final_status": final_status,
                "source_unchanged": initial_status == final_status,
                "python": sys.version, "model_behavior": "not-measured",
                "live_runtime": "not-run"}
    save("identity.json", identity)
    print(json.dumps({"identity": identity, "coverage": len(inventory),
                      "export_targets": [x["target"] for x in exports],
                      "routing_disagreements": [x["id"] for x in routes if x["expectation_met"] is False],
                      "task_package_cases": [{"id": x["id"], "errors": x["errors"]}
                                             for x in contract["cases"]]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
