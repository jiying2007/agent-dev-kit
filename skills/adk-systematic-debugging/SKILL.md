---
name: adk-systematic-debugging
description: "用于根因不明问题的复现、单变量实验、sanitizer 取证与回归；不用于跳过取证猜修复或替代性能基准。"
version: 1.2.4
last_updated: 2026-11-16
triggers:
  - "调试"
  - "排查问题"
  - "故障定位"
  - "代码有问题"
  - "诊断循环"
  - "根因排查"
  - "问题排查"
  - "定位根因"
  - "真实问题排查"
  - "根因未明"
  - "失败定位"
  - "sanitizer 取证"
  - "UBSan 取证"
non_triggers:
  - 已有明确根因且只需执行已确认修复
  - 纯文档或命名修改
inputs:
  - 现象描述、触发条件、日志与监控证据
outputs:
  - 假设矩阵、实验记录、repair note、根因结论与修复验证证据
constraints:
  - 先做只读诊断，未经确认不做破坏性操作
  - 单轮仅验证一个假设并记录正负结果
  - 没有证据链不得给出根因结论
  - 禁止在未缩小失败范围时盲目重试或扩大改动
---

# adk-systematic-debugging

## Goal
定位根因并验证修复。

## Prerequisites
固定版本/环境/输入/时间窗、指标与日志；先只读，破坏性操作保持原授权边界。

## 方法选择
- 直接因果链明确时记录复现/原因/修复，不虚构假设或负结果。
- 多根因按概率/影响/证伪成本排序；强现象链用 5-Why，每层有证据，到可验证根因即停。
- 范围大、回归引入点未知或假设穷尽时，二分代码/配置/模块/输入，逐步记 good/bad；矛盾先查测试信号。

## Workflow
1. 固定现象/影响/触发，建立会因缺陷转红的最小信号。困难/偶现读 `references/tight-feedback-loop.md` 核复现率与误报；替代信号标 `proxy evidence`，无安全复现方式记 blocker。
2. 单变量实验留时间线、命令/输入、观察/反例/不可重复路径，收缩失败范围。E2/E3 正确性/安全关键前提做适用证伪，可复用同身份证据，不强制加 Agent。
3. **Repair Note**：failed scope、preserved passing scope、minimal rerun、rollback anchor、风险、root cause status。格式失败修 schema/模板；语义失败固定断言；并行只 reopen 失败项；设备不稳先固化环境，保留通过产物。
4. 映射观察与根因，执行同条件“复现 -> 修复 -> 回归”并核原通过路径。连续两轮无信息增量则停，重审信号/假设；5-Why 断链先补证。未收敛保持 `needs-fix`。

## 按需取证
- 内存/UB/数据竞争：读 `references/sanitizer-validation.md` 核目标/runtime 与已知缺陷对照；UBSan 报警即使 exit 0 也不能通过。
- UBIFS/SquashFS、Buildroot/Autotools、Wi-Fi/DNS/MQTT、SPI/QSPI、FOC：读 `references/embedded-diagnosis-branches.md` 选择下一证据，不替代 BSP/TRM 或现场记录。
- AI 工具/CLI 异常：对照文档版本，追源码/配置决策点，用 git log/blame 建时间线后归因。

## Commands
```bash
rg -n "error|fatal|panic|timeout|reset" <log-or-src>
```
transport/debugger 仅用已核实的只读入口；交付所选方法适用性、上述原始证据和结果，未跑记 `not-run`。
