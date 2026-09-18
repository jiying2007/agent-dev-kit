"""CLI runtime substrate: environment, compatibility bridge, and stable output I/O."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Sequence

from .model import Manifest, ManifestError


def _discover_root() -> Path:
    configured = os.environ.get("ADK_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    candidates = [Path.cwd()] + list(Path(__file__).resolve().parents)
    for candidate in candidates:
        if (candidate / "manifest.json").is_file() and (candidate / "scripts" / "devkit.sh").is_file():
            return candidate.resolve()
    return Path.cwd().resolve()


ROOT = _discover_root()
DEFAULT_TASKS = ROOT / "tests" / "fixtures" / "product_eval_tasks.jsonl"



PUBLIC_COMMANDS = [
    ("validate", "校验 canonical manifest 与资产结构"),
    ("manifest", "只读检查 canonical manifest composition"),
    ("doctor", "只读检查运行环境与 M5-ready 前置条件"),
    ("catalog", "生成或检索 Agent/Skill 目录"),
    ("match", "按 Skill Content v2 语义匹配 Skill 路由"),
    ("phase-context", "解析语义 phase context"),
    ("skill-relationships", "解析 typed Skill relationships 与 delivery lifecycle"),
    ("export", "确定性导出 direct target 资产"),
    ("target", "检查或执行 direct target contract smoke"),
    ("install", "plan/apply/rollback 安装事务"),
    ("lock", "检查或显式清理 target writer lock"),
    ("benchmark", "运行或展示资产平台性能基准"),
    ("security", "执行阻断式资产与发布安全检查"),
    ("eval", "运行确定性或真实运行时评测"),
    ("release", "检查、构建或发布制品"),
    ("test", "运行完整回归测试"),
    ("goal", "检查 ADK 目标契约"),
    ("capability", "检查 ADK 能力健康"),
    ("harness", "检查目标仓 Harness readiness"),
    ("task-cost", "生成确定性任务成本与执行预算 receipt"),
    ("propose", "创建或推进变更提案"),
    ("apply", "应用已批准变更"),
    ("verify", "验证变更与证据"),
    ("review", "执行变更审查"),
    ("archive", "归档已闭环变更"),
]


def _manifest() -> Manifest:
    if not (ROOT / "manifest.json").is_file():
        raise ManifestError("ADK asset root not found; run inside a checkout or set ADK_ROOT")
    return Manifest.load(ROOT)


def _json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def _write_json(path: Path, value: Any) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="." + path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    ) as stream:
        temp = Path(stream.name)
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    try:
        os.replace(str(temp), str(path))
    finally:
        temp.unlink(missing_ok=True)


def _write_text(path: Path, value: str) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="." + path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    ) as stream:
        temp = Path(stream.name)
        stream.write(value)
    try:
        os.replace(str(temp), str(path))
    finally:
        temp.unlink(missing_ok=True)


def _help() -> None:
    print("Usage:")
    print("  ./scripts/devkit.sh <command> [options]")
    print("")
    print("Commands:")
    for name, description in PUBLIC_COMMANDS:
        print("  {:24s} {}".format(name, description))
