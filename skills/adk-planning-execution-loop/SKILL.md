---
name: adk-planning-execution-loop
description: "用于按已批准多阶段计划实际执行、定向验证、断点恢复与目标收敛；不用于只读计划审查、CI 等待查询或生成 Goal 合同。"
version: 1.4.3
last_updated: 2026-11-11
triggers:
  - "执行计划"
  - "按现有计划继续执行"
  - "分阶段执行"
  - "恢复执行已批准任务"
  - "失败阶段回退"
non_triggers:
  - "只要计划不要执行"
  - "仅查询CI状态"
  - "生成Goal合同"
  - "单文件低风险修改"
inputs:
  - 已批准计划、当前 Goal 状态、权限、验证命令和停止条件
outputs:
  - 实际交付及证据、最小检查点、收敛或阻塞回执
constraints:
  - 原验收及权限不自动扩大，完成声明需独立验证
  - 不自行调整宿主预算或制造进展证据
---

# 长任务分阶段执行

## Goal
按既有 Goal/计划连续交付**真实通过验收的子项**，而不是反复计划、总结或轮询；ADK Skill 只提供方法，Goal 权威和执行许可归宿主/Execution Policy。

## Workflow
1. **恢复**：先读唯一 current-state、原验收 ID、最后真实 commit/验证回执和最多 3 个下一动作。已有计划只读取差异，不重建 Goal、历史或权限。
2. **选择**：选 1–4 个依赖已满足、可关闭的纵向交付；明确文件/工具边界、证据、最小验证和停止条件。单文件简单修复无需启动完整长任务流程。
3. **预检**：优先使用宿主的真实事件/状态指纹；CI pending、无新证据、已成功的同状态工具/验证交给确定性执行器，不重新调用模型。同 Goal/阶段无实质变化不重复推理；高风险、缺失或来源不可信时回读原文并审核。
4. **执行**：围绕当前批次推进，可连续完成相关小改并跑定向测试；批末运行受影响回归，原 Goal 最终完成才运行整体 final。共享契约/权限/发布边界变化立即升级原门禁。
5. **检查点**：只保存当前验收、`logical_task_open`、实质变化、新证据 raw_ref、未解阻塞、来源 SHA 和下一动作。默认 ≤8 KiB、最多 3 个下一动作；长日志和旧对话外部可回读，不反复注入模型。
6. **收敛**：相同失败两次先修正假设；`design-change` 或连续两轮新 blocker/major finding class 须 replan；无有效进展、预算 stop 或真实 blocker 时 replan/split/blocked。不能靠心跳、重复证据、改编号或提预算清零，须改变依赖/范围/验收/验证路径并核效果。
7. **验收**：核对原验收分母、证据来源、未关闭项和独立验证；阶段 checkpoint 不完成父 Goal、不授予 commit/apply/release。外部写入结果不明时先对账再重试。

## Commands
仅在适用阶段、且已验证 ADK 源路径后使用：
```bash
rtk bash scripts/devkit.sh goal state-check --state <current.json> --summary-json
rtk bash scripts/devkit.sh verify --change <change-id>
```

## Failure Handling
只读 CI 状态/heartbeat 无变化就停止本轮推理；有 READY 的独立项可继续，缺失目标执行权限则交还宿主。安全、并行资源冲突、受控生命周期、事故恢复、完整 attestation/验收字段详见按需 [长任务恢复与安全边界](references/long-task-recovery.md)。

## Quality Gate
每个关闭项都有真实验证；规划/研究/原型不得擅自实施。来源事件不能代替审批，摘要不能代替原文审核；受控全生命周期审查和 `adk-verification-before-completion` 仍适用。无真实运行时用量不声明 Token 节省；不设每日费用硬限额。
