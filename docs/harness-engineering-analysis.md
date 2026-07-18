# Harness Engineering 吸收决策与当前实现

**状态**：current

**复核日期**：2026-07-17

**适用范围**：`agent-dev-kit` platform-neutral control plane

**关联变更**：`docs/changes/harness-team-readiness-v1/`

本文替代 2026-05-13 的初版差距分析。初版把多项后来已经落地的能力继续写成“未来建议”，并保留了一套与 `docs/changes/` 并行的目录和质量门禁示例。当前结论以 manifest、可执行 checker 和验证证据为准，不以文章术语或目录外观为准。

## 1. 来源与证据等级

| 来源 | 等级 | retrieved_at | review_status | expires_at | 用途 |
|---|---|---|---|---|---|
| [OpenAI — Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/) | primary | 2026-07-17 | reviewed | 2026-10-15 | 仓库知识、渐进披露、机械门禁、可观测性和 entropy control 的一级依据 |
| 用户在会话中提供的《驾驭 AI Coding：一份面向团队的 Harness Engineering 落地规范》摘录 | secondary | 2026-07-17 | review-required | 2026-10-15 | 提炼团队落地场景；原始文章 URL 与发布日期未提供，不用于声明官方事实 |
| `reports/wechat-absorb-batch-2026-05-23-p0-005.md`、`reports/wechat-absorb-batch-2026-05-23-p2-reference-001.md` | local evidence | 2026-07-17 | reviewed | 2026-10-15 | 证明 Harness 方法论已被 method-only 吸收，避免重复 Skill 和 runtime |

用户摘录中引用的其他公众号链接只说明配图来源，不能代替该摘录本身的原始 URL。若后续取得原始 URL，应走独立 intake、去重、许可证和来源复核，不反向改写本次已验证的工程事实。

## 2. 吸收结论

### 2.1 实质吸收

以下模式与 ADK 边界一致，已落到可执行或可审查资产：

1. 仓库作为长期事实源：根/局部 `AGENTS.md`、`docs/`、manifest 和 change artifacts 共同承载稳定上下文。
2. 渐进式披露：L1/L2/L3 context layers 和按需 Skill 路由，避免巨型常驻 Prompt。
3. Spec/plan 一等工件：`docs/changes/<change-id>/` 与 `propose -> apply -> verify -> review -> archive` 状态机。
4. 机械门禁：strict validation、workflow closure、capability health、tests、security 与 completion verification。
5. 工具和权限边界：MCP 显式清单、read-only-first、凭证运行时注入、外部写操作审批。
6. 状态、恢复与证据：state/history、negative results、Evidence Index、install rollback 和分支/发布治理。
7. entropy control：文档同步、格式、catalog、routing 和 freshness 检查。
8. 团队 readiness 投影：`devkit.sh harness readiness` 用七个无权重维度检查任意目标仓的可见证据。

### 2.2 合并到现有能力，不新建平行资产

| 二级文章概念 | ADK canonical 承载 | 决策 |
|---|---|---|
| Planner / Generator / Evaluator / Archiver | 稳定职责 Agent + planning / review / verification / archive Skills 与 workflow | MERGE；不复制阶段型角色 |
| Rules / Skills / MCP / Knowledge Base | `AGENTS.md`、manifest、Skills、MCP governance、Knowledge Hub 路由 | MERGE；保持工具中立 |
| requirements/task/archive | `docs/changes/` 和 workflow state machine | MERGE；不引入 `.codebuddy/plan/` 作为 core |
| harness-audit Skill | typed readiness core + fixtures + capability health | REPLACE；机械事实不用 Prompt 判定 |
| 团队规范同步仓 | source-to-live / export / install contract | OBSERVE；没有独立部署需求前不创建新仓 |

### 2.3 明确拒绝

- 拒绝 7 维加权 100 分：总分会掩盖权限泄漏、恢复缺失等关键短板。ADK 使用 `blocked > needs-review > partial > pass` 最短板优先模型。
- 拒绝 AI 代码占比、提交量等 KPI：这些指标可被刷高且不能证明业务正确性、可维护性或现场可靠性。
- 拒绝默认接入 MCP：没有真实外部数据需求时是 `not-applicable`，不是扣分项。
- 拒绝把聊天历史或自动 memory 当事实源：项目事实必须回到 Git/Hub 的受治理工件。
- 拒绝复制 CodeBuddy/Knot 内网配置、token 示例和 `@latest` 依赖到通用 core。
- 拒绝宣称“完全自主”“自动回滚到稳定状态”或“效率提升固定百分比”，除非有对应运行时、现场和对照实验数据。

## 3. 当前能力映射

| Harness 问题 | ADK 当前实现 | 证据入口 | 当前边界 |
|---|---|---|---|
| AI 应看到什么 | root/local AGENTS、context layers、manifest、changes、Knowledge Hub preflight | `manifest.json`、`docs/context-*`、`docs/changes/` | 不自动灌入全部知识 |
| AI 能触达什么 | 显式 tools/MCP/runtime contracts | `docs/runbooks/mcp-governance.md`、runtime capability contracts | 默认不安装、不外写 |
| 按什么顺序执行 | workflow、goal、state transition、planning loop | `scripts/workflow.sh`、workflow manifests | 不是通用 Agent runtime |
| 如何保持连续性 | state/history、negative results、handoff、Hub candidate | change artifacts、Knowledge Hub | memory 不能覆盖 current facts |
| 如何判断正确 | tests、eval、review、Evidence Index、verification gate | `tests/`、`scripts/evidence-index.sh` | 现场证据与模拟证据分开 |
| 如何约束和恢复 | permission/approval、installer rollback、Git/change trace | security/installer/change contracts | 不自动执行破坏性恢复 |
| 如何控制熵增 | doc/catalog/format/routing/freshness checks | `scripts/check-*.sh`、capability health | 仍需 owner 和周期性治理 |

## 4. Harness Readiness v1 合同

`harness readiness` 是证据投影，不是架构评分器。固定维度为：

1. `context_legibility`
2. `spec_and_execution_contract`
3. `tool_and_permission_boundary`
4. `state_and_knowledge_continuity`
5. `verification_review_and_eval`
6. `recovery_and_rollback`
7. `freshness_and_entropy_control`

每个维度输出：

- `status`：`pass|partial|needs-review|blocked|not-applicable`
- `evidence_refs`：实际命中的仓库相对路径
- `last_verified_at`：项目显式记录的验证时间，没有则为 `not-recorded`；未来或超过 90 天 freshness 窗口时产生 blocker
- `owner`：项目显式记录的责任人，没有则为 `unassigned`
- `blockers`：稳定问题码与脱敏位置
- `next_action`：最小改进动作

默认模式只报告；显式 `--gate` 才要求总状态为 `pass`。扫描不执行目标仓脚本、不访问网络、不跟随 symlink；检测到敏感配置时只返回 key path，不返回值。存在 MCP 时，`pass` 要求 metadata 中有结构化只读、审批和凭证来源合同，文档关键词只作补充且否定语境不计为正证据。

## 5. Canonical 入口

```bash
# ADK 自身 harness/loop 合同
bash scripts/devkit.sh harness-loop-engineering --summary-json

# 任意目标仓 Harness readiness
bash scripts/devkit.sh harness readiness --root /path/to/repo --summary-json
bash scripts/devkit.sh harness readiness --root /path/to/repo --output report.md
bash scripts/devkit.sh harness readiness --root /path/to/repo --gate
bash scripts/devkit.sh harness readiness --root /path/to/repo --as-of 2026-07-18 --summary-json

# ADK 变更生命周期
bash scripts/devkit.sh propose --change <id> --title "说明"
bash scripts/devkit.sh apply --change <id>
bash scripts/devkit.sh verify --change <id>
bash scripts/devkit.sh review --change <id> --result pass --blockers 0 --majors 0 --minors 0
```

`docs/changes/` 是唯一 canonical change workspace。根 `changes/` 和 `scripts/quality-gates.sh` 只保留兼容迁移说明/包装层，不再定义另一套工件结构。

## 6. 仍需真实证据的事项

- 30 天以上、至少两个真实仓库、至少两个 operator 的团队试点。
- readiness 误报/漏报、扫描耗时、修复 lead time 和 blocker 复发率。
- 独立仓库中的恢复演练、权限拒绝事件和验证 freshness。
- 原公众号文章 URL、发布日期和许可边界。

这些项目只能标为 planned/open evidence，不能从 fixture、单仓本地测试或文章案例推导为生产成熟度。

## 7. 维护规则

- 路由或维度变化先改 `manifests/harness_readiness_contracts.json` 与测试，再同步本文。
- 机械规则只检查可重复事实；需要架构判断的内容保持 `needs-review`，不塞进脆弱的关键词“智能评分”。
- 新增 MCP/connector 前必须审查 transport、凭证、权限、deny-path、日志脱敏和 fallback。
- 每次完成 readiness 行为变更必须保留至少一个负向 fixture 与命令级 Evidence Index。
- 官方来源到期、行为变化或试点证据形成时重新复核；不得静默把 reviewing candidate 提升为 active。
