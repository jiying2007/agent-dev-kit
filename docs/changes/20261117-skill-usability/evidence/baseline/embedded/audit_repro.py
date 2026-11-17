"""Read-only source audit and bounded host controls for the embedded Skill group.

All writes are confined to this audit directory or unittest-owned temporary dirs.
This script provides no device/native Agent-runtime qualification.
"""
from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import unittest

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
BASE = Path("/workspace/scratch/fe8de3b42084")
ROOT = BASE / "adk-skill-usability"
OUT = BASE / "skill-usability-audit/embedded"
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from agent_dev_kit._matcher_kernel import _frontmatter
from agent_dev_kit.compiler import export_assets
from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest


NATURAL_TASKS = {
    "adk-register-map-design": "按参考手册整理 UART 寄存器映射，说明 W1C 与复位有效位。",
    "adk-bsp-analysis": "梳理这个 BSP 的启动、probe、clock/reset 依赖和历史 patch，不修改代码",
    "adk-driver-implementation": "实现 RTOS SPI 驱动，补超时、取消和资源回收路径。",
    "adk-driver-bringup-checklist": "STM32 首板联调，需要核对 SPI 屏时钟、复位和最小收发。",
    "adk-bsp-porting-playbook": "规划从旧板到新板的 BSP 移植和可恢复启动验证。",
    "adk-rtos-task-design": "请设计 RTOS 任务优先级、周期和共享资源。",
    "adk-interrupt-dma-patterns": "排查 Cortex-M7 的 DMA 读到旧数据问题，只审 ownership 和 cache。",
    "adk-protocol-stack-integration": "设计通信协议状态机，覆盖部分收发、超时和恢复。",
    "adk-cmake-cross-build": "用 CMake 交叉编译 ARM 工程，核对工具链和测试后端。",
    "adk-embedded-debug-transport": "核对设备调试通道的串口、SSH 和 GDB remote 连接条件。",
    "adk-embedded-remote-debug-log-triage": "设备失联后收集远程调试和设备日志线索，只读取证。",
    "adk-hardware-debugging": "MCU 随机 HardFault，请列有证据的排查步骤。",
    "adk-performance-profiling-embedded": "只做嵌入式性能分析，定位 CPU 和内存瓶颈。",
    "adk-unit-test-embedded": "为 STM32 固件消息队列补单测，覆盖满队列和取消。",
    "adk-integration-hil-sil": "设计 HIL/SIL 集成测试，区分模拟与板端覆盖。",
    "adk-embedded-diagnostic-harness": "诊断 harness 需要区分 invoke_ret 的预期失败与真实缺陷。",
    "adk-fault-injection-recovery": "设计故障注入测试，验证内存分配失败后的资源回收。",
    "adk-static-analysis-c-cpp": "对嵌入式 C++ 代码做静态分析，追踪头文件告警。",
    "adk-embedded-release-orchestration": "准备 MCU 固件包和嵌入式发布编排，只做本地制品检查。",
    "adk-embedded-storage-layout-migration": "评估 UBIFS 转 SquashFS 存储布局迁移和数据保留。",
}

BOUNDARIES = [
    ("rtos-nonengineering", "请做一个季度销售团队任务设计。", None),
    ("rtos-explicit-baremetal", "项目没有 RTOS；请评估裸机主循环任务设计。", None),
    ("rtos-positive-control", "请设计 RTOS 任务优先级、周期和共享资源。", "adk-rtos-task-design"),
    ("dma-polling-cache", "SPI DMA 轮询已经满足已量化 latency/CPU budget 的场景，仍需检查 DMA cache coherency。", "adk-interrupt-dma-patterns"),
    ("dma-budget-fragment", "请检查 DMA 缓存一致性，这是受 CPU budget 的场景限制的系统。", "adk-interrupt-dma-patterns"),
    ("dma-cache-positive-control", "SPI DMA 读到旧数据，请检查 DMA cache coherency。", "adk-interrupt-dma-patterns"),
    ("static-prototype-explicit", "请对这个 C++ 快速原型验证代码运行静态分析，查找越界和泄漏。", "adk-static-analysis-c-cpp"),
    ("static-positive-control", "请对这个 C++ 代码运行静态分析，查找越界和泄漏。", "adk-static-analysis-c-cpp"),
    ("remote-local-only", "请分析这份本地设备日志，只使用我提供的文本，不连接设备。", None),
    ("remote-positive-control", "设备失联后需要远程调试，检查设备日志和 transport。", "adk-embedded-remote-debug-log-triage"),
]


def routes():
    manifest = Manifest.load(ROOT)
    inventory = json.loads((BASE / "skill-usability-audit/groups.json").read_text())["groups"]["embedded"]
    coverage = []
    for item in inventory:
        metadata = _frontmatter(ROOT / item["path"])
        positive = match_text(manifest, metadata["triggers"][0], skill=item["name"], scope="skill")
        negative = match_text(manifest, metadata["non_triggers"][0], skill=item["name"], scope="skill")
        task = NATURAL_TASKS[item["name"]]
        natural = match_text(manifest, task)
        coverage.append(dict(name=item["name"], path=item["path"],
                             explicit_positive=positive, explicit_negative=negative,
                             task=task, auto_result=natural,
                             auto_expected_match=natural.get("skill") == item["name"]))
    boundaries = []
    for identifier, prompt, expected in BOUNDARIES:
        result = match_text(manifest, prompt)
        diagnostic_skill = expected
        if identifier.startswith("rtos-"):
            diagnostic_skill = "adk-rtos-task-design"
        elif identifier.startswith("remote-"):
            diagnostic_skill = "adk-embedded-remote-debug-log-triage"
        diagnostic = (match_text(manifest, prompt, skill=diagnostic_skill, scope="skill")
                      if diagnostic_skill else None)
        boundaries.append(dict(id=identifier, prompt=prompt, expected=expected,
                               result=result, isolated_result=diagnostic))
    return dict(coverage=coverage, boundaries=boundaries)


def rta_counterexample():
    """Literal transcription of the published hp-only recurrence, not an RTOS."""
    skill = (ROOT / "skills/adk-rtos-task-design/SKILL.md").read_text()
    formula = "Rnext = Ci + Bi + sum(ceil(R / Tj) * Cj, j in higher-priority tasks) + Ii(R)"
    if formula not in skill:
        raise ValueError("published formula changed; re-review before replay")

    def response(task, tasks):
        current = task["C"]
        values = [current]
        for _ in range(100):
            following = task["C"] + sum(math.ceil(current / other["T"]) * other["C"]
                                        for other in tasks if other["priority"] > task["priority"])
            values.append(following)
            if following == current or following > task["D"]:
                return dict(iteration=values, R=following, passes=following <= task["D"])
            current = following
        raise AssertionError("counterexample did not converge within the bound")

    equal = [dict(name="A", C=6, T=10, D=10, priority=2),
             dict(name="B", C=6, T=10, D=10, priority=2)]
    distinct = [dict(name="A", C=2, T=10, D=10, priority=2),
                dict(name="B", C=3, T=10, D=10, priority=1)]
    wrong = [response(task, equal) for task in equal]
    control = [response(task, distinct) for task in distinct]
    required_work, available_cpu_time = 12, 10
    assert all(row["passes"] for row in wrong)
    assert required_work > available_cpu_time
    assert [row["R"] for row in control] == [2, 5]
    return dict(evidence_level="host arithmetic; no RTOS or hardware measurement",
                published_formula=formula,
                counterexample=dict(tasks=equal, B=0, I=0, formula_result=wrong,
                                    synchronous_release_time=0, common_deadline=10,
                                    required_work=required_work, available_cpu_time=available_cpu_time,
                                    feasible=False),
                applicable_control=dict(tasks=distinct, B=0, I=0, formula_result=control))


def exported_assets():
    manifest = Manifest.load(ROOT)
    names = set(NATURAL_TASKS)
    observations = []
    for target in ("claude-code", "opencode"):
        result = export_assets(manifest, target, OUT / "exports", ["embedded-fullstack"])
        consumer = Path(result["output"])
        rows = []
        for name in sorted(names):
            candidates = [p for p in consumer.rglob("SKILL.md") if p.parent.name == name]
            if len(candidates) != 1:
                raise AssertionError((target, name, candidates))
            path = candidates[0]
            text = path.read_text()
            references = []
            for source in sorted((ROOT / "skills" / name / "references").glob("*.md")):
                destination = path.parent / "references" / source.name
                references.append(dict(path=str(destination.relative_to(consumer)),
                                       exists=destination.is_file(),
                                       exact_copy=destination.read_bytes() == source.read_bytes()))
            source_body = (ROOT / "skills" / name / "SKILL.md").read_text().split("---", 2)[2]
            target_body = text.split("---", 2)[2]
            rows.append(dict(name=name, destination=str(path.relative_to(consumer)),
                             body_preserved=source_body == target_body, references=references,
                             bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        assert len(rows) == 20
        assert all(row["body_preserved"] and all(ref["exact_copy"] for ref in row["references"]) for row in rows)
        observations.append(dict(target=target, status=result["status"], group_skill_count=len(rows), skills=rows))
    return observations


def selected_tests():
    tests = [
        "tests.test_skill_domain_execution",
        "tests.test_skill_rtos_methods",
        "tests.test_skill_cmake_methods",
        "tests.test_skill_command_examples.BspBuildExampleTests",
        "tests.test_skill_command_examples.CmakeBuildExampleTests",
        "tests.test_skill_command_examples.CtestQualificationExampleTests",
        "tests.test_skill_command_examples.CtestReportReaderTests",
        "tests.test_skill_fault_activation",
        "tests.test_skill_runtime_methods.RunningObjectEvidenceTests",
        "tests.test_external_domain_methods.PublishedDomainExamplesTests.test_public_state_sequence_replays_and_rejects_the_bug",
        "tests.test_external_domain_methods.PublishedDomainExamplesTests.test_public_gcc_stack_example_exposes_dynamic_part",
    ]
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        suite = unittest.defaultTestLoader.loadTestsFromNames(tests)
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (OUT / "targeted-tests.log").write_text(stream.getvalue())
    return dict(tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                skipped=result.skipped, success=result.wasSuccessful(), selection=tests,
                log=str(OUT / "targeted-tests.log"))


if __name__ == "__main__":
    action = sys.argv[1]
    operations = dict(routes=routes, rta=rta_counterexample, exports=exported_assets, tests=selected_tests)
    result = operations[action]()
    record = dict(source="78c3be7f6f9b5ee2e557de54156532fb3169198d",
                  observed_at=datetime.now(timezone.utc).isoformat(), action=action, result=result)
    path = OUT / (action + ".json")
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(output=str(path), result=result if action in ("rta", "tests") else "recorded"),
                     ensure_ascii=False))
