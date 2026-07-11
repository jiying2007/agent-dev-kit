---
name: adk-code-review-loop
description: 独立代码审查与反馈修复闭环，覆盖发现分级、真实性核验、修复验证和复审
version: 1.3.0
last_updated: 2026-07-11
triggers:
  - "独立代码审查"
  - "code review loop"
  - "review 闭环"
  - "审查反馈"
  - "复审"
  - "收到 review"
  - "修复 review"
non_triggers:
  - 纯格式化且已有自动格式检查
  - 提交前只需要校验 commit message
inputs:
  - diff、需求目标、测试结果、review 发现、修复范围
outputs:
  - 分级发现、真实性判定、修复任务、复审结论和剩余风险
constraints:
  - 不得盲目接受 review 结论
  - blocker 和 major 未闭环不得给 pass
  - 审查者发现问题不等于修复者可以扩大范围
---

# adk-code-review-loop

## Goal
- 将代码审查从一次性意见列表变成可验证闭环。
- 对标 Superpowers 的 requesting/receiving review 能力，但保持 adk-first 的证据和门禁格式。
- 区分真实缺陷、风格建议、误报和超范围建议，避免盲修。

## Prerequisites
- 已有明确 diff 或变更文件清单。
- 已知道本次变更目标和非目标。
- 已收集基本验证结果，至少知道相关测试是否可运行。
- 若 review 来自 CI/AI runner，必须有结构化 findings、trusted-trigger/secret 隔离决策和 SCM 发布边界。

## 发现分级

| 级别 | 定义 | 处理 |
|---|---|---|
| blocker | 会导致错误、安全问题、数据损坏或发布阻断 | 必须修复或明确接受风险 |
| major | 明显质量风险、边界遗漏、可复现回归 | 默认修复 |
| minor | 可读性、命名、局部风格或后续优化 | 可延期但需记录 |
| question | 信息不足或假设不明 | 先澄清，不直接改 |
| cannot-verify-from-diff | 需求依赖未改动代码、外部行为或运行态证据，仅凭 diff 无法判定 | 由主 Agent 或 owner 补查，不得默认为通过 |

## Workflow
1. **重述变更目标**：确认 review 对照的是正确需求，而不是泛泛挑刺。
2. **读取 diff 与测试**：按文件查看实际改动和验证证据。
3. **列出发现**：每条发现包含文件、位置、现象、影响和建议；检查异常分支、边界条件、权限/安全、兼容性、数据正确性、测试缺口和复杂度。
4. **双 verdict 审查**：同时给出 spec-compliance verdict 与 quality verdict；同一次阅读 diff 覆盖需求符合性和代码质量，不重复派发多个局部 reviewer。
5. **Review context 固定**：记录 review 对照的需求包、领域模型、非目标、验证基线和变更范围；缺少这些上下文时先标记 `question` 或 `cannot-verify-from-diff`，不得补脑通过。
6. **真实性核验**：判断问题是否可复现、是否有代码证据、是否属于本次范围；不能从 diff 判定的项标记为 `cannot-verify-from-diff`。
7. **分级裁决**：按 blocker/major/minor/question/cannot-verify-from-diff 分类。
8. **生成修复任务**：每个 blocker/major 对应一个最小修复动作和验证命令。
9. **执行或交接修复**：修复不得顺带重构无关文件。
10. **复审**：修复后重新检查原发现是否闭环，新增风险是否出现。
11. **整体验证**：任务级 review 通过后，仍需一次 whole-diff/whole-branch 视角检查跨任务集成问题。
12. **门禁交接**：将结论交给 `adk-commit-pr-quality-gate` 或 `adk-verification-before-completion`。
13. **CI/PR 发布核验**：若要发布 SCM comment，必须按 `manifests/pr_review_governance_contracts.json` 验证 schema-backed findings、untrusted PR 隔离和 inline anchoring。
14. **Review 改进闭环**：重复 review 失败模式只能作为 trace-feedback-eval-handoff 候选进入 AAR，不得直接改 durable guidance。

## Review Report Template
```md
- Review Scope:
- Requirement Baseline:
- Domain Model Baseline:
- Verification Baseline:
- Review Mode: task-level | whole-diff | whole-branch
- Spec Verdict:
- Quality Verdict:
- Findings:
  | ID | Severity | File | Evidence | Required Action | Status |
  |---|---|---|---|---|---|
- Cannot Verify From Diff:
- False Positives:
- Out-of-scope Suggestions:
- CI/PR Review Boundary:
  - trusted_trigger:
  - protected_secret_exposure:
  - structured_output_valid:
  - inline_anchor_valid:
- Fix Plan:
- Re-review Result:
- Final Verdict: pass | needs-fix
```

补充样例模板：`references/review-feedback-fixtures.md`，用于记录误报、越界建议和复审证据。

## Commands
```bash
# 查看变更范围
git diff --stat
git diff --name-only

# 查看指定文件 diff
git diff -- <path>

# 运行相关验证
<project-test-command>
```

## Failure Handling
- review 反馈不清楚时，先重写为可验证命题；仍不清楚则标记 question。
- 发现与需求无关时，记录为 out-of-scope，不混入本次修复。
- 修复后验证失败时，切换到 `adk-systematic-debugging` 定位。
- 若 review 要求改 shared contract/schema，先回到 `adk-requirements-triage` 和 `adk-task-breakdown`。

## Quality Gate
- 每个 blocker/major 必须有状态：fixed、accepted-risk、not-applicable。
- pass 结论必须满足 blocker=0 且 major=0。
- pass 结论还必须处理 `cannot-verify-from-diff`：补验证证据、owner 接受风险或明确不适用。
- 缺少 Requirement Baseline、Domain Model Baseline 或 Verification Baseline 时，不得给出 spec-compliance pass；必须先补上下文或降级为 `cannot-verify-from-diff`。
- reviewer 不得修改工作树、切换分支或执行破坏性操作；审查默认只读。
- reviewer 不得被要求忽略发现、预设严重级别或接受 implementer rationale 作为证据。
- 误报必须说明证据，不得只写“不认同”。
- 复审必须引用修复后的验证命令或代码证据。
- 提交/PR 前必须再过 `adk-commit-pr-quality-gate`。
- AI review 只能作为第一轮风险扫描；高风险、业务语义或 owner 责任结论必须由人类 reviewer 或明确 owner 最终确认。
- 机器发布 review comment 前必须有 schema-backed findings；不能从自由文本直接生成 SCM 写 payload。
- fork/public PR 默认不接收 protected secrets；没有 trusted-trigger 决策时只允许只读分析。
- inline comment 位置无法验证时，必须降级为 summary finding。
- 重复 review 模式若要提升为规则，必须有 sanitized trace、eval candidate、validation result 和 human approval。

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "review 说了就改" | review 也可能误判或越界 | 先做真实性和范围核验 |
| "都是 minor 不用记" | minor 多了会形成技术债 | 记录可延期项和 owner |
| "修一个顺手重构一片" | 容易制造新风险 | 每条发现对应最小修复 |
