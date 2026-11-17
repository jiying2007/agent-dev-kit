"""Reproducible source inventory and no-model routing audit; no product writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = "6d902f721f560f02883516e809fbd93a326405b6"
REPO = Path("/workspace/scratch/d417066aafa8/agent-dev-kit")
OUT = Path(__file__).resolve().parent

# Decisions follow manual full-text review of each body and every direct reference.
REASONS = {
    "adk-runtime-router": ("fix", "SK-01,SK-02,SK-03", "唯一 primary、按需加载与权限上限保留；canonical matcher 的否定、动作/主题和驱动修饰语有可复现反例。"),
    "adk-context-engineering": ("retain-with-method-gap", "SK-04", "稳定/任务/证据/按需层与 raw fallback 已清楚；压缩后 active Skill 正文有效性恢复未明确，属于方法缺口，未证明模型失败。"),
    "adk-token-context-governance": ("retain", "", "区分 source bytes、真实 Token 与成本；预算、例外、原始证据回取齐全。正文较长本身不足以证明压缩收益。"),
    "adk-requirements-triage": ("retain", "", "brief 与执行交接按风险区分，明确复用既有授权和事实，不强制重复问询。"),
    "adk-structured-requirements-questioning": ("retain", "", "Explore 单问、Challenge 依赖前沿、稳定问题 ID 和失效传播完整；原型范围与收敛条件清楚。"),
    "adk-repo-prompt-analysis": ("retain", "", "追踪真实提示加载链和来源身份，不把外部内容当执行授权。"),
    "adk-skill-deep-analysis": ("retain", "", "有界发现、来源、权限和 holdout 评估齐备，实施交接与研究结论分开。"),
    "adk-lightweight-planning": ("retain", "", "只要计划时保持只读；步骤按任务最小化，未强制固定步数或治理工件。"),
    "adk-task-breakdown": ("retain", "", "任务包字段、scope 映射与外层信封一致；分阶段兼容迁移例可操作。"),
    "adk-parallel-agent-governance": ("retain", "", "并发依据收益、资源与依赖；唯一写者、独立复核和数据型交接明确。"),
    "adk-worktree-governance": ("fix", "SK-01", "正文尊重不建 worktree、用户脏改和清理权限；内核仍会将被禁止创建的短别名选为 primary。"),
    "adk-context-compress-handoff": ("retain-with-method-gap", "SK-04", "最新目标/排除项/授权/raw pointer/下三步保留；缺 active Skill 正文已丢失时的来源核验与重载指导。"),
    "adk-interface-contract-design": ("fix", "SK-02", "生命周期、版本能力、schema 方言和副作用契约保留；API/接口主题在路由计分中压过明确写 ADR 动作。"),
    "adk-adr-writer": ("fix", "SK-02", "真实权衡、风险分级及冷读验收良好；裸 ADR 同时导致概念误选与主题争抢，需收紧动作边界。"),
    "adk-component-api-stability": ("retain", "", "API/ABI/行为兼容和旧二进制/重编译验证区分，未以符号表代替 ABI 证明。"),
    "adk-register-map-design": ("retain", "", "resetMask/未知位/read-safe/W1C 与读回顺序完整，避免有副作用的通用 RMW。"),
    "adk-bsp-analysis": ("retain", "", "Linux/RTOS/裸机分支和硬件/源码版本身份明确；不跨域机械套方法。"),
    "adk-goal-authoring": ("retain", "", "保留原目标与验收分母，活动前沿有界，不捏造预算或把恢复变成执行授权。"),
    "adk-planning-execution-loop": ("retain", "SK-05", "既有授权、真实推进、操作对账与小状态恢复齐备；自然表达漏选作为词法覆盖限制记录，未纳入本次 T3。"),
    "adk-driver-implementation": ("fix", "SK-03", "多 runtime 生命周期/IRQ/DMA 与设备写分权良好；只识别相邻实现驱动，漏掉 RTOS SPI DMA 修饰的真实实现请求。"),
    "adk-driver-bringup-checklist": ("retain", "", "被动/主动探测和 MMIO 效果分级，按 bring-up 阶段验证，无通用 24 小时硬门槛。"),
    "adk-bsp-porting-playbook": ("retain", "", "目标工具链、独立构建路径、CPU/RAM 并发及 last-good 恢复明确，不盲改 defconfig。"),
    "adk-rtos-task-design": ("retain", "", "响应时间分析限定固定优先级/单核假设；tick 量化和 FreeRTOS callback/queue 行为说明到位。"),
    "adk-interrupt-dma-patterns": ("retain", "", "buffer ownership、cache 方向、终止/取消、ISR 优先级与目标预算齐全。"),
    "adk-protocol-stack-integration": ("retain", "", "stream/datagram/partial I/O 与总期限、重试责任明确；空抓包不冒充成功。"),
    "adk-cmake-cross-build": ("retain", "", "工具链/构建身份、fresh JUnit、skip/disabled/not-run 与零通过处理完整；未将历史 hosted 超时归因于正文。"),
    "adk-code-simplification": ("retain", "", "保护行为与公共 seam，按问题简化而非任意行数门槛；避免清理触发语义变化。"),
    "adk-systematic-debugging": ("retain", "", "原始失败先保留、因果实验和 bisect 退出码齐全；sanitizer exit 0 仍检查诊断。"),
    "adk-embedded-debug-transport": ("retain", "", "目标身份、只读/主动/状态变更分级，GDB attach/halt 效果有说明，设备授权不隐含。"),
    "adk-embedded-remote-debug-log-triage": ("retain", "", "连接分层、ADB 语义状态、有界恢复和新身份核验完整；不可用工具不伪造实际验证。"),
    "adk-offline-core-dump-triage": ("retain", "", "精确 ELF/库/Build ID 匹配，GDB 禁自动加载；未知 frame 保留部分验证状态。"),
    "adk-hardware-debugging": ("retain", "", "镜像/模块/ELF relocation 身份和 MCU 能力边界明确，不猜地址或寄存器可用性。"),
    "adk-performance-profiling-embedded": ("retain", "", "真实 workload、交替测量、混杂因素与 PMU 语义清楚；静态栈帧不当总上界，KWS 保留流式与泄漏边界。"),
    "adk-test-strategy": ("retain", "", "按风险选择最小有意义检查、独立 oracle/错误变体与检查器校准，文本编辑不强制全量测试。"),
    "adk-unit-test-embedded": ("retain", "", "域条件和 host/compile-only/SIL/HIL 区分；FIFO 示例有状态探索且不受 PYTHONOPTIMIZE 关闭断言影响。"),
    "adk-integration-hil-sil": ("retain", "", "fresh JUnit、选择数/通过/跳过/未跑分开，硬件范围与 mutation 授权分离。"),
    "adk-embedded-diagnostic-harness": ("retain", "", "expected nonzero 与执行错误、strict 与环境前置失败分开，未放宽初始化错误。"),
    "adk-fault-injection-recovery": ("retain", "", "实际激活命中与配置区分，缺恢复时间标未知；下一检查默认 host-safe，设备写需另授。"),
    "adk-artifact-gating": ("retain", "", "workflow 与真实状态区分，Root 专有脚本明确限定消费环境。"),
    "adk-pilot-framework": ("retain", "", "smoke/效果比较/连通性与实际任务分开，不强迫外部项目运行 ADK 私有脚本。"),
    "adk-verification-before-completion": ("retain", "", "checkpoint/goal-final 与原分母、适用风险/fresh source 区分，25 项按需检查不是一律门禁。"),
    "adk-code-review-loop": ("retain", "", "反馈核实与全量 diff/lifecycle 区分，精确快照含 dirty overlay，Spec/Quality 独立且评论不当权限。"),
    "adk-repo-drift-remediation": ("retain", "", "先问题映射再改动，真实脚本路径与根目录核验，保护用户脏改。"),
    "adk-static-analysis-c-cpp": ("retain", "", "真实编译数据库/翻译单元/header 依赖、扫描器退出码与 baseline 安全明确，零 TU 不当通过。"),
    "adk-commit-pr-quality-gate": ("retain", "", "message-only 与 PR/high-risk readiness 区分，复用有效证据而不重造授权。"),
    "adk-release-versioning": ("retain", "", "完整 commit body/revert、祖先/浅克隆核验与不可变 tag 边界，版本推断默认只读。"),
    "adk-production-field-readiness": ("retain", "", "限定量产/现场领域，artifact/目标测试/OTA 证据真实分层；人分钟与墙钟区分。"),
    "adk-embedded-release-orchestration": ("retain", "", "prepare/publish/flash 分权，多 MCU 部分失败需真实设备回执。"),
    "adk-embedded-storage-layout-migration": ("retain", "", "日志分析不当迁移；PEB/LEB/容量几何核验、数据卷保留与写前 host dry-run 明确。"),
    "adk-cross-team-handoff": ("retain", "", "lite/formal 依风险，冷读条件具体，不伪造接收方验收。"),
    "adk-branch-closeout": ("retain", "", "精确 HEAD/checks/授权复用、实际 main 后验齐备；清理破坏性不隐式获批。"),
    "adk-after-action-review": ("retain", "", "轻量复盘和升格分开，来源/脱敏/候选状态保留，不凭总结捏造收益。"),
    "adk-memory-curator": ("retain", "", "默认报告、来源冲突和文件名式 secret scan，禁止无授权持续保存。"),
    "adk-archive-governance": ("retain", "", "区分旧/新 hash 与来源变化，不盲认补 hash；既有 owner/授权可复用。"),
    "adk-knowledge-archive": ("retain", "", "归档要有可复用价值和可达路径，不将敏感 raw 或候选自动升格。"),
    "adk-engineering-growth-review": ("retain", "", "范围有界、重复证据与归因分开，额外评测只在能力升格时要求。"),
    "adk-external-practice-absorption": ("retain", "", "source/decision/implementation 边界清楚，已批准代码任务不重复 intake；长正文不等于已证实成本缺陷。"),
    "adk-data-fetch": ("retain", "", "可选子技能单独安装和权限，pass/partial/not-verified 保真。"),
    "adk-email-imap-fetch": ("retain", "", "EXAMINE/UIDVALIDITY/UID/BODY.PEEK 与日期时区过滤、精确地址核验到位，不标已读或发送。"),
    "adk-fetch-url-content": ("retain", "", "IP 校验绑定真实连接、重定向/Host/SNI 与预算/robots/type/partial 语义完整。"),
    "adk-test-flakiness-triage": ("retain", "", "实际 case 数与进程退出区分，有界复跑和零失败置信界正确，不以反复绿色抹平失败。"),
    "adk-security-supply-chain": ("retain", "", "source-only/安装/runtime 范围分层，覆盖清单及 source-sink/隐式序列化泄漏检查完整，扫描不当认证。"),
    "adk-prose-revision": ("retain", "", "局部修改保全事实/限定语，不使用 AI detector；无问题不硬造 3–5 处修改。"),
    "adk-incident-rca-report": ("retain", "", "事实/原因/假设、发生/观察时间及钟差区分；5 why 可选，不捏造负责人。"),
    "adk-skill-composition-governance": ("retain", "", "collision-only 与全组合审查区分，复用 canonical matcher；真实行为/holdout/负效果与 source-byte 边界保留。"),
}

PROBES = (
    ("SK-01", "不要创建 worktree，在当前分支直接实现该修复", None, "adk-worktree-governance"),
    ("SK-01", "Do not create a worktree. Implement the fix in the current branch.", None, "adk-worktree-governance"),
    ("SK-01", "Never create a new worktree; use the current branch.", None, "adk-worktree-governance"),
    ("control", "不要头脑风暴，请创建 worktree 实现修复", "adk-worktree-governance", None),
    ("control", "不要创建 worktree；之后需要 worktree 隔离实现", "adk-worktree-governance", None),
    ("SK-02", "请写ADR，记录接口契约的设计取舍", "adk-adr-writer", None),
    ("SK-02", "把这个 API 设计决定写成 ADR，不修改代码", "adk-adr-writer", None),
    ("SK-02", "请更新 ADR，记录 API设计 的兼容取舍", "adk-adr-writer", None),
    ("SK-02", "请将设计接口时确定的错误码方案记录为 ADR", "adk-adr-writer", None),
    ("SK-02", "只读解释 ADR 概念", None, "adk-adr-writer"),
    ("SK-02", "什么是 ADR？", None, "adk-adr-writer"),
    ("control", "按 ADR 实现接口契约", "adk-interface-contract-design", "adk-adr-writer"),
    ("control", "不要写 ADR，请设计接口并验证兼容性", "adk-interface-contract-design", "adk-adr-writer"),
    ("SK-03", "请实现 RTOS SPI DMA 驱动，补超时和恢复测试", "adk-driver-implementation", None),
    ("SK-03", "请为 Linux 实现 I2C 驱动", "adk-driver-implementation", None),
    ("SK-03", "只读评估实现 RTOS SPI DMA 驱动的方案", "adk-driver-implementation", None),
    ("control", "解释 RTOS SPI DMA 驱动的原理", None, "adk-driver-implementation"),
    ("control", "不要实现 RTOS SPI DMA 驱动，只做代码审查", "adk-code-review-loop", "adk-driver-implementation"),
    ("control", "请实现 Selenium 浏览器驱动", None, "adk-driver-implementation"),
)


def git_bytes(path: str) -> bytes:
    return subprocess.run(["git", "show", f"{BASE}:{path}"], cwd=REPO, check=True, capture_output=True).stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("inventory", "probe"))
    parser.add_argument("--root", type=Path, default=REPO)
    parser.add_argument("--label", default="current")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).isoformat()
    if args.mode == "inventory":
        manifest = json.loads(git_bytes("manifest.json"))
        tracked = subprocess.run(["git", "ls-tree", "-r", "--name-only", BASE], cwd=REPO, check=True, capture_output=True, text=True).stdout.splitlines()
        rows = []
        reference_paths = set()
        for section in ("skills", "optional_skills"):
            for entry in manifest[section]:
                decision, findings, rationale = REASONS[entry["name"]]
                body = git_bytes(entry["path"])
                refs = []
                prefix = str(Path(entry["path"]).parent / "references") + "/"
                for path in tracked:
                    if path.startswith(prefix):
                        data = git_bytes(path)
                        refs.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "review": "full-text"})
                        reference_paths.add(path)
                rows.append({"skill_id": entry["name"], "scope": section, "path": entry["path"], "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body), "body_review": "full-text", "decision": decision, "findings": findings.split(",") if findings else [], "rationale": rationale, "direct_references": refs})
        assert len(rows) == 65 and len({r["skill_id"] for r in rows}) == 65
        assert set(REASONS) == {r["skill_id"] for r in rows}
        assert len(reference_paths) == 54
        value = {"schema": "adk-source-skill-audit/v1", "baseline_commit": BASE, "baseline_version": "11.3.14", "recorded_at": stamp, "coverage": {"skill_bodies": len(rows), "core": 56, "optional": 9, "direct_references": len(reference_paths)}, "limits": ["All body/reference text reviewed; not every behavioral scenario executed", "Local deterministic matcher evidence only; no model, native-runtime, paid invocation, hardware or HIL evidence", "Retain means no substantiated issue found in this bounded review, not proof of absence", "Source bytes are inventory, not observed model tokens or cost"], "skills": rows}
        target = OUT / "skills-audit.json"
    else:
        sys.path.insert(0, str(args.root / "src"))
        from agent_dev_kit.matcher import match_text
        from agent_dev_kit.model import Manifest

        manifest = Manifest.load(args.root)
        rows = []
        for finding, prompt, expected, prohibited in PROBES:
            result = match_text(manifest, prompt, scope="auto")
            okay = (expected is None or result.get("skill") == expected) and (prohibited is None or result.get("skill") != prohibited)
            rows.append({"finding": finding, "prompt": prompt, "expected_skill": expected, "prohibited_skill": prohibited, "satisfies_expected_selection": okay, "result": result})
        tracked_inputs = ["manifest.json", "src/agent_dev_kit/_matcher_kernel.py", "src/agent_dev_kit/matcher.py", "manifests/skill_content_contracts_v2.json", "skills/adk-adr-writer/SKILL.md", "skills/adk-driver-implementation/SKILL.md", "skills/adk-worktree-governance/SKILL.md"]
        value = {"schema": "adk-source-routing-probes/v1", "baseline_commit": BASE, "label": args.label, "source_root": str(args.root), "recorded_at": stamp, "python": sys.version, "source_sha256": {p: hashlib.sha256((args.root / p).read_bytes()).hexdigest() for p in tracked_inputs}, "total": len(rows), "passed": sum(r["satisfies_expected_selection"] for r in rows), "probes": rows, "qualification": "deterministic source matcher only; no runtime/model/device calls"}
        target = OUT / f"routing-{args.label}.json"
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(target), "coverage": value.get("coverage"), "total": value.get("total"), "passed": value.get("passed")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
