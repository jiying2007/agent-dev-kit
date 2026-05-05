---
name: task-breakdown
description: 将需求拆解为可并行执行的任务包
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 任务过大或多人协作时
  - 需要评估是否适合并行开发时
non_triggers:
  - 单点微调任务
  - 单文件小修且无共享依赖变更
inputs:
  - 需求范围、里程碑、模块边界与依赖关系
outputs:
  - 任务清单、依赖图、优先级、ownership 与冲突矩阵
constraints:
  - 每个任务必须可独立验证
  - 默认禁止两个任务并行修改同一 shared contract/schema
---

# task-breakdown

## Goal
- 把复杂需求拆成边界清晰、可独立验收的任务包。

## Prerequisites
- 已有需求包和至少一个可执行验收标准。
- 明确共享文件、共享 contract 和根配置触点。

## Workflow
1. 定义拆分边界：明确 scope_write、scope_read、输入输出与完成标准。
2. 并行准入判断：检查是否存在同文件写冲突、共享 contract、根配置冲突。
3. 生成任务包：每个任务给出 owner、依赖、验证命令与阻塞条件。
4. 定义交接令牌：每个任务声明 `ready_to_handoff` 条件与接收方。
5. 轻量工件：输出 `需求梳理`、`task checklist`、`执行反馈/验收记录` 三段模板。
6. 规划整合顺序：列出 merge order、联调点与最终统一验证步骤。
7. 大仓触点梳理：若涉及大型多模块仓，补关键触点清单（scripts/entry/command registry/shared contract）。
8. 输出执行建议：适合并行则给 2-4 个任务包，不适合则给单线程方案。

## Commands
```bash
rg -n "contract|schema|shared|entry|router|package.json" <repo_root>
git diff --name-only <base>...HEAD
```

## Evidence Template
```md
- Parallel Suitability: yes/no
- Task Packages (owner/scope/dependency):
- Work Mode (diagnosis/repro/planning/execution):
- Handoff Token (ready_to_handoff + receiver):
- Lightweight Artifacts (需求梳理/task checklist/执行反馈):
- Large-Repo Touchpoints (scripts/entry/command-registry/shared-contract):
- Conflict Matrix:
- Merge Order:
- Final Integration Verification:
```

## Failure Handling
- 若拆分后冲突面扩大，降级为单线程执行方案。
- 若出现未识别共享依赖，暂停并重新划分 scope。

## Quality Gate
- 每个任务必须具备独立验证命令与可交付产物。
- 必须显式标记共享文件/共享 contract 冲突面。
- 每个任务必须声明 handoff 条件，避免“完成定义”不一致。
- 必须给出“适合并行/不适合并行”的明确结论与理由。
- 必须给出当前推进模式与收敛条件，避免持续空转分析。

---

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "拆太细浪费时间" | 粗粒度任务导致并行冲突和集成地狱 | 按 SKILL.md 流程拆到可独立验证的粒度 |
| "我一个人做不需要拆任务" | 单人也会遗忘依赖和边界，任务拆解是思维工具 | 即使单人也按流程输出任务包和 handoff 条件 |
| "反正做着做着会调整" | 无计划的调整是失控的委婉说法 | 先完成任务拆解再执行，调整需记录变更原因 |
