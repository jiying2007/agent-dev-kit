# 标准工作流模板 (Standard Workflow Template)

> **使用场景**: 适用于正常的功能开发、Bug 修复、重构等非紧急变更流程。
> **状态机**: proposed → applied → verified → review-passed → archived
> **核心原则**: 每个阶段必须满足退出条件后才能进入下一阶段，不可跳过。

---

## 工作流概述

> **何时使用**: 适用于正常的功能开发、Bug 修复、重构等非紧急变更流程。如遇生产环境 P0/P1 故障，请改用 emergency-workflow-template。

标准工作流定义了 global-dev-kit 中变更从提出到归档的完整生命周期。
包含 5 个阶段，每个阶段有明确的 Entry Criteria（进入条件）、执行步骤和 Exit Criteria（退出条件）。

---

## Stage 1: Propose (提出变更)

**目的**: 定义变更的范围、目标和技术方案。

**Entry Criteria**:
- [ ] 变更需求已确认（需求来源明确）
- [ ] 已识别相关利益方

**执行步骤**:
1. 创建变更分支或工作目录
2. 编写/更新 design-spec（设计规格文档）
3. 编写 implementation-plan（实施计划）
4. 如有架构变更，更新 system-arch（系统架构文档）
5. 编写 task-breakdown（任务分解）

**产出物**:
- design-spec (status: DRAFT)
- implementation-plan (status: DRAFT)
- task-breakdown (status: DRAFT)

**Exit Criteria**:
- [ ] 设计文档已通过团队评审
- [ ] 实施计划已确认（时间线、资源、风险已知）
- [ ] 所有 Open Questions 已有结论或跟进计划
- [ ] 产出物状态更新为 READY

---

## Stage 2: Apply (实施变更)

**目的**: 按照实施计划执行代码变更。

**Entry Criteria**:
- [ ] Propose 阶段产出物状态为 READY
- [ ] 开发环境已准备就绪
- [ ] 依赖项已确认可用

**执行步骤**:
1. 按 task-breakdown 中的任务顺序开发
2. 编写代码和对应单元测试
3. 本地构建和测试通过
4. 更新相关文档（API 文档、README 等）
5. 提交代码到变更分支

**产出物**:
- 代码变更（commits）
- 单元测试
- 更新的文档

**Exit Criteria**:
- [ ] 所有计划任务已完成
- [ ] 本地测试全部通过
- [ ] 代码符合项目编码规范
- [ ] 无遗留的 lint/格式警告
- [ ] commit message 格式规范

---

## Stage 3: Verify (验证变更)

**目的**: 通过自动化测试和手动验证确保变更正确且无回归。

**Entry Criteria**:
- [ ] Apply 阶段代码已提交
- [ ] CI 构建成功
- [ ] 测试环境可用

**执行步骤**:
1. 运行完整测试套件（单元测试 + 集成测试）
2. 执行覆盖率检查
3. 如涉及嵌入式，执行 HIL/SIL 测试
4. 执行性能基准测试（如适用）
5. 手动验证关键路径
6. 生成 test-report（测试报告）

**产出物**:
- test-report (status: READY)
- 覆盖率报告
- 性能基准数据（如适用）

**Exit Criteria**:
- [ ] 所有测试通过（通过率 ≥ 95%）
- [ ] 无新增 Critical/Major Bug
- [ ] 覆盖率指标达标
- [ ] test-report 已完成

---

## Stage 4: Review (审查变更)

**目的**: 对代码和文档进行系统性审查，确保质量。

**Entry Criteria**:
- [ ] Verify 阶段 test-report 为 READY 且 PASS
- [ ] 审查人已指定
- [ ] 代码变更已准备好供审查

**执行步骤**:
1. 审查人检视代码变更（正确性、设计、安全性）
2. 审查文档完整性
3. 审查测试充分性
4. 输出 review-report（审查报告）
5. 如有 NEEDS-FIX 问题，返回 Apply 阶段修复后重新 Verify
6. 修复完成后重新审查
7. 编写 approval-document（审批文档）
8. 获取必要的签核

**产出物**:
- review-report (verdict: PASS)
- approval-document (status: APPROVED)

**Exit Criteria**:
- [ ] review-report 结论为 PASS
- [ ] 所有 Critical Issues 已修复
- [ ] approval-document 已获得所有必要签核
- [ ] 无遗留的阻塞性问题

---

## Stage 5: Archive (归档变更)

**目的**: 将验证通过的变更合入主干并归档所有产出物。

**Entry Criteria**:
- [ ] Review 阶段所有签核已获取
- [ ] approval-document 状态为 APPROVED
- [ ] 无遗留的阻塞性问题

**执行步骤**:
1. 合入变更分支到主干（merge/rebase）
2. 更新 CHANGELOG
3. 打标签（tag）或创建发布版本（如适用）
4. 归档所有产出物到 docs/runbooks/
5. 更新 Evidence Index
6. 通知相关团队变更已完成
7. 清理临时分支

**产出物**:
- 合入主干的代码
- 更新的 CHANGELOG
- 归档的文档集（design-spec + test-report + review-report + approval）

**Exit Criteria**:
- [ ] 代码已合入主干
- [ ] CI 构建通过
- [ ] 所有产出物已归档
- [ ] Evidence Index 已更新
- [ ] 相关团队已通知
- [ ] 临时分支已清理

---

## 状态转换规则总结

```
propose  →  applied        (propose exit criteria met)
applied  →  verified       (verify exit criteria met)
verified →  review-passed  (review exit criteria met)
review-passed → archived   (archive exit criteria met)
```

**回退规则**:
- Review 阶段 NEEDS-FIX → 回退到 Apply 阶段
- Verify 阶段测试失败 → 回退到 Apply 阶段
- 任何阶段发现设计缺陷 → 回退到 Propose 阶段
