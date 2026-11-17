"""Bounded independent recheck of the identified first/then regression."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest

ROOT = Path("/workspace/scratch/d417066aafa8/agent-dev-kit")
POSITIVES = (
    ("先说明方案再实现驱动", "adk-driver-implementation", "workspace-write"),
    ("先说明方案再实现 RTOS SPI DMA 驱动", "adk-driver-implementation", "workspace-write"),
    ("先解释隔离价值再创建 worktree", "adk-worktree-governance", "deny"),
    ("请先解释取舍再更新 ADR", "adk-adr-writer", "deny"),
    ("请先解释取舍然后更新 ADR", "adk-adr-writer", "deny"),
)
NEGATIVES = (
    ("解释为什么再实现 RTOS SPI DMA 驱动", "adk-driver-implementation"),
    ("解释为何再更新 ADR", "adk-adr-writer"),
    ("请先解释为什么再实现 RTOS SPI DMA 驱动", "adk-driver-implementation"),
    ("请先说明怎样先分析再实现驱动", "adk-driver-implementation"),
    ("请先解释是否再创建 worktree", "adk-worktree-governance"),
    ("先说明方案再不要实现驱动", "adk-driver-implementation"),
    ("先说明方案再解释如何实现驱动", "adk-driver-implementation"),
)


if __name__ == "__main__":
    manifest = Manifest.load(ROOT)
    rows = []
    for prompt, expected, permission in POSITIVES:
        result = match_text(manifest, prompt)
        rows.append({"prompt": prompt, "expected_skill": expected, "expected_permission": permission,
                     "matches_expectation": result.get("skill") == expected and result.get("mutation_permission") == permission,
                     "result": result})
    for prompt, prohibited in NEGATIVES:
        result = match_text(manifest, prompt)
        rows.append({"prompt": prompt, "prohibited_skill": prohibited, "expected_permission": "deny",
                     "matches_expectation": result.get("skill") != prohibited and result.get("mutation_permission") == "deny",
                     "result": result})
    print(json.dumps({"observed_at": datetime.now(UTC).isoformat(), "cases": len(rows),
                      "satisfied": sum(row["matches_expectation"] for row in rows), "observations": rows,
                      "source_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                                        for path in ("src/agent_dev_kit/_matcher_kernel.py", "src/agent_dev_kit/matcher.py", "manifest.json")}},
                     ensure_ascii=False, indent=2))
