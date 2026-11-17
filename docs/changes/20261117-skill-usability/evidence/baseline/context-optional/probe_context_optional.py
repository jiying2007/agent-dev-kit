"""Read-only ADK Skill audit probes; outputs live outside the source repository.

These deterministic probes do not invoke a native agent, remote service,
installation target, or model evaluator. Exported bundles are local fixtures.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import yaml

from agent_dev_kit.compiler import export_assets
from agent_dev_kit.matcher import match_text, resolve_skill_content
from agent_dev_kit.model import Manifest
from agent_dev_kit.targets import render_selection


ROOT = Path("/workspace/scratch/fe8de3b42084/adk-skill-usability")
AUDIT = Path("/workspace/scratch/fe8de3b42084/skill-usability-audit/context-optional")
GROUPS = AUDIT.parent / "groups.json"
RTK = "/workspace/scratch/fe8de3b42084/verification-tools/rtk"
BASELINE = "78c3be7f6f9b5ee2e557de54156532fb3169198d"


def frontmatter(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


def run() -> dict:
    manifest = Manifest.load(ROOT)
    selected = json.loads(GROUPS.read_text(encoding="utf-8"))["groups"]["context_optional"]
    head = subprocess.run(
        [RTK, "git", "rev-parse", "HEAD"], cwd=ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if head != BASELINE:
        raise RuntimeError(f"baseline changed: {head}")

    coverage = []
    for item in selected:
        path = ROOT / item["path"]
        metadata = frontmatter(path)
        scope = "optional-skill" if item["path"].startswith("optional-skills/") else "skill"
        files = []
        for child in sorted(path.parent.rglob("*")):
            if child.is_file() and not any(parent.name.startswith("adk-")
                    for parent in child.relative_to(path.parent).parents if parent != Path(".")):
                files.append({"path": child.relative_to(ROOT).as_posix(),
                              "sha256": hashlib.sha256(child.read_bytes()).hexdigest()})
        coverage.append({
            **item,
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "line_count": len(path.read_text(encoding="utf-8").splitlines()),
            "content_contract": resolve_skill_content(manifest, item["name"]),
            "files": files,
            "explicit_positive": [
                {"text": text, "result": match_text(manifest, text, skill=item["name"], scope=scope)}
                for text in metadata["triggers"]
            ],
            "explicit_negative": [
                {"text": text, "result": match_text(manifest, text, skill=item["name"], scope=scope)}
                for text in metadata["non_triggers"]
            ],
            "automatic_positive": [
                {"text": text, "result": match_text(manifest, text)}
                for text in metadata["triggers"]
            ],
        })

    prompts = {
        "archive-repair": "请修复归档元数据，已明确授权修改 docs/archive 的 topic 和 meta，不删除历史文件。",
        "archive-readonly-control": "请检查已有归档元数据，先给只读报告。",
        "archive-unknown-hash": "请只读分析归档 hash mismatch，差异尚未核实，不要重算或修改原 hash。",
        "context-engineering-distinct-task": "我需要上下文工程：只整理稳定规则、按需引用和跨会话证据指针，不做 token 配额治理。",
        "context-omission-control": "上下文工程",
        "context-explicit-exclusion": "上下文工程，不要使用 adk-token-context-governance",
        "execution-continuation": "按现有计划继续执行",
        "goal-readonly": "只读计划，不要生成Goal合同",
        "goal-new-contract": "生成Goal合同",
        "rca-active-incident": "线上事故，服务仍不可用，请先排查。",
        "rca-recovered": "故障复盘：服务已经恢复，请整理 RCA。",
        "imap-explicit-name": "使用 adk-email-imap-fetch 获取邮件",
    }
    cases = {key: {"input": value, "result": match_text(manifest, value)}
             for key, value in prompts.items()}
    cases["context-explicit-control"] = {
        "input": prompts["context-omission-control"],
        "result": match_text(manifest, prompts["context-omission-control"],
                             skill="adk-context-engineering", scope="skill"),
    }

    optional = [item["name"] for item in selected
                if item["path"].startswith("optional-skills/")]
    exports = []
    for target in ("claude-code", "opencode"):
        output_parent = AUDIT / "fixtures" / "exports"
        if (output_parent / target).exists():
            raise RuntimeError("refuse to overwrite existing audit export; choose a fresh directory")
        exported = export_assets(manifest, target, output_parent, ["core"], optional, "skill")
        output = Path(exported["output"])
        bundle_skills = sorted(path.parent.name for path in output.rglob("SKILL.md"))
        source_command = subprocess.run(
            [RTK, "bash", "scripts/devkit.sh", "catalog", "find", "--keyword", "adk", "--type", "skill"],
            cwd=output, capture_output=True, text=True, check=False, timeout=10,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        exports.append({
            "target": target,
            "output": str(output),
            "status": exported["status"],
            "selected_skill_presence": {item["name"]: item["name"] in bundle_skills
                                        for item in selected},
            "source_helper_presence": {
                relative: (output / relative).exists() for relative in
                ("scripts/devkit.sh", "manifest.json", "manifests/token_context_policy.json",
                 "schemas/agent-handoff-v1.schema.json", "templates/planning/worker-contract.md")
            },
            "published_composition_command": {
                "argv": ["bash", "scripts/devkit.sh", "catalog", "find", "--keyword", "adk", "--type", "skill"],
                "returncode": source_command.returncode,
                "stdout": source_command.stdout,
                "stderr": source_command.stderr,
            },
        })

    optional_isolation = []
    for target in ("claude-code", "opencode"):
        for requested in (["adk-data-fetch"], ["adk-fetch-url-content"],
                          ["adk-data-fetch", "adk-fetch-url-content"]):
            bundle = render_selection(manifest, target, ["core"], requested, "skill")
            optional_isolation.append({
                "target": target, "requested": requested,
                "fetch_files": [item.destination for item in bundle.files
                                if "fetch" in item.destination],
            })

    return {
        "baseline": BASELINE,
        "observed_head": head,
        "evidence_level": "source-contract and deterministic local fixture; native behavior not-measured",
        "python": sys.version,
        "coverage": coverage,
        "cases": cases,
        "exports": exports,
        "optional_isolation": optional_isolation,
    }


if __name__ == "__main__":
    result = run()
    destination = AUDIT / "probe-results.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(destination),
        "covered_skills": len(result["coverage"]),
        "explicit_positives": sum(len(row["explicit_positive"]) for row in result["coverage"]),
        "explicit_negatives": sum(len(row["explicit_negative"]) for row in result["coverage"]),
        "exports": [{"target": row["target"], "status": row["status"],
                     "source_command_rc": row["published_composition_command"]["returncode"]}
                    for row in result["exports"]],
    }, ensure_ascii=False))
