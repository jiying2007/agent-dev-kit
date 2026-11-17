"""Acceptance-derived matcher probes for T3a; never a native runtime test."""
from __future__ import annotations
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path("/workspace/scratch/fe8de3b42084/adk-skill-usability")
sys.path.insert(0, str(ROOT / "src"))
from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest

RTOS = "adk-rtos-task-design"
BSP = "adk-bsp-analysis"
DMA = "adk-interrupt-dma-patterns"
CASES = [
    ("rtos-valid", "请设计 RTOS 任务优先级、周期和共享资源。", RTOS, True),
    ("rtos-freertos", "请为 FreeRTOS 做实时任务设计。", RTOS, True),
    ("rtos-sales", "请做一个季度销售团队任务设计。", RTOS, False),
    ("rtos-absent", "项目没有 RTOS；请评估裸机主循环任务设计。", RTOS, False),
    ("bsp-fixture", "梳理这个 BSP 的启动、probe、clock/reset 依赖和历史 patch，不修改代码", BSP, True),
    ("bsp-existing-soc", "SoC board 迁移分析", BSP, True),
    ("bsp-generic", "梳理这个季度的销售目标和人员安排。", BSP, False),
    ("bsp-porting", "请规划 BSP 移植和启动链迁移。", BSP, False),
    ("bsp-driver", "BSP 的接口已明确，请直接实现驱动。", BSP, False),
    ("dma-budget", "请检查 DMA 缓存一致性，这是受 CPU budget 的场景限制的系统。", DMA, True),
    ("dma-polling", "SPI DMA 轮询已经满足已量化 latency/CPU budget 的场景，仍需检查 DMA cache coherency。", DMA, True),
    ("dma-none", "无中断且无 DMA 的纯轮询任务，只需评估普通循环。", DMA, False),
]

manifest = Manifest.load(ROOT)
records = []
for name, prompt, skill, should_select in CASES:
    result = match_text(manifest, prompt)
    selected = result.get("match") is True and result.get("skill") == skill
    records.append(dict(id=name, prompt=prompt, skill=skill, should_select=should_select,
                        actual=result, pass_case=selected == should_select))
print(json.dumps(dict(cases=records, passed=sum(row["pass_case"] for row in records),
                      total=len(records)), ensure_ascii=False, indent=2))
raise SystemExit(0 if all(row["pass_case"] for row in records) else 1)
