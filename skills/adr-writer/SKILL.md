---
name: adr-writer
description: 产出 Architecture Decision Record 并固化技术决策
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "写ADR"
  - "架构决策"
  - "决策记录"
non_triggers:
  - 临时性小修补
inputs:
  - 候选方案、约束、风险
outputs:
  - ADR 文档草稿
constraints:
  - 必须包含 trade-off 和 rejected options
---

# adr-writer

## Goal
- 形成可追溯的架构决策记录，避免“口头拍板”。

## Prerequisites
- 明确决策范围（一个 ADR 只解决一个核心问题）。
- 收集至少 2 个可行候选方案与现实约束。

## Workflow
1. 定义问题陈述：背景、目标、非目标、成功标准。
2. 构建方案矩阵：复杂度、性能、成本、迁移难度逐项对比。
3. 记录 rejected options：说明不选原因与适用边界。
4. 写明决策后果：短期收益、长期债务、触发重评条件。
5. 绑定验证计划：如何证明该决策成立。

## Evidence Template
```md
# ADR-XXX: <title>
- Context:
- Decision:
- Alternatives Considered:
- Rejected Options + Reasons:
- Consequences:
- Verification Plan:
- Rollback Trigger:
```

## Failure Handling
- 信息不足时输出 `needs-fix`，列出缺失字段，不进入拍板。
- 方案收益无法量化时，回退到最小可行方案并标注风险。

## Quality Gate
- ADR 必须包含 Context/Decision/Alternatives/Consequences 四段。
- 必须有至少一个 rejected option 与对应理由。
- 验证计划与回退触发条件不可为空。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
