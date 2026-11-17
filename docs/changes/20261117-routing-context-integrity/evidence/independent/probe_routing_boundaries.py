"""Independent action/negation probes derived from the change's acceptance text."""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from agent_dev_kit.matcher import format_result, match_text
from agent_dev_kit.model import Manifest

ROOT = Path(os.environ.get("ADK_REVIEW_ROOT", "/workspace/scratch/d417066aafa8/agent-dev-kit"))
CASES = (
    ("worktree-negative-zh", "不要创建 worktree，直接修复当前分支的代码", "avoid", "adk-worktree-governance"),
    ("worktree-negative-git-modifier", "不要创建新的 Git worktree，直接修复当前分支的代码", "avoid", "adk-worktree-governance"),
    ("worktree-negative-new", "不创建新工作树，直接修复当前分支的代码", "avoid", "adk-worktree-governance"),
    ("worktree-negative-en", "Do not create a worktree; 直接修复当前分支", "avoid", "adk-worktree-governance"),
    ("worktree-negative-en-git", "Don't create a git worktree; 直接修复当前分支", "avoid", "adk-worktree-governance"),
    ("worktree-negative-en-any", "Do not create any worktree; 直接修复当前分支", "avoid", "adk-worktree-governance"),
    ("worktree-positive-unrelated-denial", "不要更新 ADR，请创建 worktree 修复驱动", "select", "adk-worktree-governance"),
    ("worktree-positive-after-negative", "不要创建 worktree 做文档；创建 worktree 修复驱动", "select", "adk-worktree-governance"),
    ("adr-action-interface-topic", "请修订 ADR 来说明接口契约和 API设计 的取舍", "select", "adk-adr-writer"),
    ("adr-action-negative-interface", "不要修改接口契约；请更新 ADR", "select", "adk-adr-writer"),
    ("adr-negative-competing-action", "别更新 ADR；按既有决定设计接口", "select", "adk-interface-contract-design"),
    ("adr-explanation", "请解释编写 ADR 的方法", "avoid", "adk-adr-writer"),
    ("adr-concept-only", "解释 ADR 概念及适用场景", "avoid", "adk-adr-writer"),
    ("adr-explanation-quoted-action", "只读解释“更新 ADR”这个术语与接口契约的关系", "avoid", "adk-adr-writer"),
    ("adr-explanation-why", "请解释为什么更新 ADR 有助于接口契约追溯", "avoid", "adk-adr-writer"),
    ("adr-author-explanatory-content", "请编写 ADR，解释接口契约的取舍", "select", "adk-adr-writer"),
    ("adr-explain-then-author", "解释 API设计 的风险，然后请更新 ADR", "select", "adk-adr-writer"),
    ("adr-negated-explanation-positive-author", "不要解释如何编写 ADR，请直接编写 ADR", "select", "adk-adr-writer"),
    ("adr-review-implementation", "只读审查代码中的更新 ADR 实现", "avoid", "adk-adr-writer"),
    ("driver-rtos-spi-dma", "实现一个 RTOS SPI-DMA 驱动，补足超时恢复", "select", "adk-driver-implementation"),
    ("driver-linux", "请实现 Linux kernel I2C 驱动", "select", "adk-driver-implementation"),
    ("driver-negative-long-phrase", "不要实现新的 RTOS SPI DMA 驱动；只读分析日志", "avoid", "adk-driver-implementation"),
    ("driver-readonly", "只读分析如何实现 RTOS SPI DMA 驱动", "deny", "adk-driver-implementation"),
    ("driver-explanation", "解释 RTOS SPI DMA 驱动中的资源生命周期", "avoid", "adk-driver-implementation"),
    ("driver-explanation-how", "请解释如何实现 RTOS SPI DMA 驱动", "deny", "adk-driver-implementation"),
    ("driver-explanation-design", "请说明怎样实现一个 RTOS SPI 驱动", "deny", "adk-driver-implementation"),
    ("driver-implementation-explanatory-output", "请实现 RTOS SPI DMA 驱动，并解释设计取舍", "select", "adk-driver-implementation"),
    ("driver-positive-after-denied-explanation", "不要解释驱动原理；请实现 RTOS SPI DMA 驱动", "select", "adk-driver-implementation"),
    ("driver-outside-domain", "请实现销售业绩驱动的推荐系统", "avoid", "adk-driver-implementation"),
    ("driver-cross-clause", "请实现接口。后面介绍 RTOS SPI DMA 驱动", "avoid", "adk-driver-implementation"),
)


def run():
    manifest = Manifest.load(ROOT)
    observations = []
    for label, prompt, check, skill in CASES:
        result = match_text(manifest, prompt)
        if check == "select":
            accepted = result.get("skill") == skill
        elif check == "avoid":
            accepted = result.get("skill") != skill
        else:
            accepted = result.get("mutation_permission") == "deny"
        observations.append({"case": label, "prompt": prompt, "expectation": {check: skill},
                             "meets_expectation": accepted, "result": result, "formatted": format_result(result)})
    return {"observed_at": datetime.now(UTC).isoformat(), "root": str(ROOT), "cases": len(observations),
            "satisfied": sum(row["meets_expectation"] for row in observations), "observations": observations}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
