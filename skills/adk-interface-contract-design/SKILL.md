---
name: adk-interface-contract-design
description: "用于模块 API、协议消息及生命周期状态转换的接口契约设计与迁移评审；不用于需求未收敛时直接写实现或放行设备动作。"
version: 1.3.7
last_updated: 2026-11-16
triggers:
  - "设计接口"
  - "API设计"
  - "接口契约"
non_triggers:
  - 纯内部重命名
inputs:
  - 调用方与被调方约束
  - 有状态或异步操作的生命周期约束（如适用）
outputs:
  - 接口或生命周期操作契约草案
constraints:
  - 必须明确输入、输出、错误码
  - 机器消费接口必须声明 strict schema、additionalProperties=false 和 refusal handling
  - 受控生命周期操作必须明确唯一 owner、状态事件和终止语义
  - 有外部副作用的工具调用和 handoff 必须在执行前完成授权，并定义恢复重放语义
---

# adk-interface-contract-design

## Goal
输出可验证的模块/嵌入式 HAL、驱动与协议栈契约，明确版本与调用方。


## Prerequisites
- 明确调用链 owner、版本策略和兼容窗口。
- 确定输入输出数据源与错误语义边界。
- 了解目标平台的内存对齐和字节序。
- 若请求会启动、取消或恢复共享资源操作，已识别唯一 owner 与状态可见性。


## Workflow
1. **接口清单**：请求、响应、错误码、幂等与异常的最小契约；C 示例按需读取 `references/details.md`。
2. **版本与能力协商**：声明消费者最低需求、提供方兼容方向及支持窗口；同 major 不保证具备新能力，版本号不证明 wire/ABI 兼容。明确增量策略的 C 例子见 `references/details.md`。
3. **错误码设计规范**：统一错误码空间，避免冲突。
   ```bash
   # 检查错误码定义一致性
   rg -n "IFACE_ERR_|ERR_" include/ src/ | sort
   # 跨文件重复字面值候选（不带文件名前缀）
   rg --no-filename -o "= -[0-9]+" include/ | sort | uniq -d
   ```
   仅覆盖该负十进制写法；宏/表达式/别名/其他进制另核。同一命名空间才判断冲突；零候选不证明无冲突。
4. **异常预算**：超时、限流、重试、降级来自目标协议、链路/设备预算与可证伪实验，不采用通用固定值。
5. **受控生命周期契约**：跨状态/独占资源操作明确唯一 owner、状态/事件/资源/终止/invariant，可见性、取消、超时、恢复、迟到完成与 generation/op-id 隔离；按需读 `references/lifecycle-operation-contract.md`。
6. **副作用**：按参数和目标在写前授权；拒绝、未知结果、重放对账见 `references/tool-effect-contract.md`。
7. **结构化输出**：机器消费的 API/消息/tool/handoff schema 声明 required fields、enum、additionalProperties=false、refusal handling 与 parse-failure。
8. **契约用例**：至少含正常/边界/异常三类断言与真实构建/测试入口；覆盖最低版本、缺必需能力和跨 major，不虚构命令。
9. **设计挑战**：高风险/长期公共接口比较两种模块边界、可见约束、演进成本与验证 seam；仅一条路径时说明限制。用反例固定术语/状态/边界，仅变化时更新既有 glossary/ADR。深模块/原型按需读 `references/design-quality-methods.md`。
10. **Spec-to-Code 双向核对**：有实现时按 `references/spec-code-bidirectional.md` 核规格→实现及可观察行为→规格；未查/未知标 `not-checked`，纯设计标待验证。

## Quality Gate
- 契约含输入/输出/错误码/超时、兼容迁移和上述 schema/用例；错误码覆盖可恢复与不可恢复场景。
- 嵌入式验证结构体大小/对齐（`pahole` 或 `sizeof` 断言）。
- 受控操作给出 owner × state × event × resource × termination × invariant 矩阵，明确 generation/op-id、幂等、重试预算、callback/cleanup 并发；缺失不得实现或判通过。副作用须有目标绑定和对账路径，审批不等于生效。

## Failure Handling
- 若调用方未确认兼容策略，结论置为 `needs-fix`。
- 若错误语义不一致，先冻结接口变更并回到设计讨论。
- 若 ABI 与线协议对齐冲突，优先区分内存表示与显式序列化，验证 `sizeof`/`offsetof`、目标架构非对齐访问和字节序；`packed` 不作为默认修复。
- 降级只选择双方明确支持且满足必需语义/能力/安全约束的交集，并记录依据；无交集或证据不明则拒绝，不能自动回退到“最低公共版本”。


## Evidence Template

```md
status: pass | needs-fix | BLOCKED
structured_schema: strict | not_applicable
lifecycle_operation: not_applicable | contract-path
commands:
- <command + exit code>
evidence:
- <path or output summary>
risks:
- <remaining risk or none>
```

状态/owner/终止不明时先冻结契约；“回调最终会完成”不能替代超时、取消和迟到完成验证。
