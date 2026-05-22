# Reference Adoption Summary（已采纳总结）

> 本文档记录"参考仓库可借鉴内容"在 `agent-dev-kit` 的落地情况，仅保留已本地化、可执行、可验证的能力。
>
> - 如需查看每个候选项的详细评估（价值/成本/风险/决策/验收状态/证据），参见 [全量评估矩阵](reference-adoption-matrix.md)。

## 1. 参考源 A（流程化上下文与证据链）

借鉴点：
- 上下文充分性检查（接口契约/风险/验证方式）
- 证据驱动结论与负结果留痕

落地点：
- `skills/adk-requirements-triage/SKILL.md`
- `skills/adk-systematic-debugging/SKILL.md`
- `scripts/workflow.sh`（`proposal.md` 强制“上下文充分性检查”）

## 2. 参考源 B（门禁与反“未验先结论”）

借鉴点：
- 完成前验证必须有证据
- 分级评审闭环（blocker/major/minor）
- 单问题变更，避免捆绑无关改动

落地点：
- `skills/adk-verification-before-completion/SKILL.md`
- `skills/adk-commit-pr-quality-gate/SKILL.md`
- `scripts/workflow.sh`（`review` 强制在 `verified` 后执行，`archive` 强制 `review-passed`）

## 3. 参考源 C（工程可维护性与边界清晰）

借鉴点：
- 以真实目录和实际依赖为准，不依赖静态假设
- 变更前明确模块边界与责任范围

落地点：
- `skills/adk-task-breakdown/SKILL.md`（`scope_write/scope_read` + ownership + 冲突矩阵）
- `scripts/workflow.sh`（`tasks.md` 强制 `Ownership 与并行冲突检查`）

## 4. 参考源 D（规格驱动与可追溯工件）

借鉴点：
- 变更工件化与状态可追溯
- 设计/任务/验证链路闭环

落地点：
- `scripts/workflow.sh`（`proposal/design/tasks/checklist/negative-results/review-report`）
- `scripts/openspec_bridge.sh`（openspec `changes/` 与 adk `docs/changes/` 双向桥接）
- `docs/workflows.md`、`docs/changes/README.md`
- `docs/runbooks/openspec-bridge.md`

## 5. 不纳入项（有意排除）

- 外部仓库特定工具链、命令约定、路径约束。
- 与本仓库目标冲突或不可本地验证的规则。
- 会引入外部依赖耦合的流程要求。

## 6. 产物标签与门禁协同

借鉴点：
- 交付物必须带标签与状态，避免跨角色交接歧义
- 门禁结论必须与测试/评审证据一致

落地点：
- `skills/adk-artifact-gating/SKILL.md`
- `docs/runbooks/artifact-gated-delivery.md`
- `manifest.yaml`（核心 skill + workflow 门禁）

结论：`agent-dev-kit` 保留“规则思想”，但全部转换为本仓库可执行脚本、模板和测试门禁，确保离线独立可用。

## 7. Codex Skills 岗位 SOP 模型（2026-05-21）

借鉴点：
- Skill 不是 prompt 升级版，而是可版本化、可审查、可复用的岗位 SOP。
- `SKILL.md` 应作为精简入口，长背景、示例和领域资料进入 `references/`。
- `description` 是 discovery 入口，必须具体、可区分、可匹配。
- Skill、Agent、Sub-agent、MCP/tool 分属方法、执行者、短生命周期执行实例和能力接口四层。
- 多 Agent 并行时，主 Agent 必须把 scope、Skill、Done criteria、验证和 report schema 作为任务契约分发。

落地点：
- `docs/skill-agent-runtime-model.md`
- `docs/skill-format-guide.md`
- `templates/planning/worker-contract.md`
- `scripts/validate-assets.sh`
- `tests/test_skill_sop_quality.sh`
- `skills/adk-parallel-agent-governance/SKILL.md`

有意排除：
- 不把第三方 Skill 安装成功视为生产采纳完成。
- 不绕过 `agent-dev-kit -> ~/codex -> ~/.codex` 声明式交付链路。
- 不把个人偏好、一次性 prompt 或外部仓库路径直接写入 adk core 规则。

## 8. Agent 记忆与 AAR 自我进化治理（2026-05-21）

借鉴点：
- Agent 记忆不等于保存聊天记录，而是保存下次同类任务会用到的偏好、项目规则、工作流和 lessons。
- 任务后必须把成功路径、失败根因、修复动作和验证证据整理为 After Action Review。
- 记忆候选需要分层：`session/user/project/lesson`，并带 `risk/confidence/evidence/last_verified/write_route`。
- 低风险可自动形成候选，高风险如自动发布、删除文件、生产数据库、支付动作、凭据保存必须人工确认。
- 记忆需要 stale / conflict / supersedes 机制，避免旧规则长期污染上下文。

落地点：
- `skills/adk-after-action-review/SKILL.md`
- `templates/memory/after-action-review.md`
- `templates/memory/memory-candidate.md`
- `docs/runbooks/memory-governance.md`
- `scripts/check-memory-governance.sh`
- `tests/test_memory_governance.sh`

有意排除：
- 不保存完整聊天记录、临时草稿、未经确认推测、密钥或隐私原文。
- 不默认引入向量库、知识图谱或数据库；先用可审查 Markdown 模板稳定结构。
- 不让 Agent 静默修改 `~/.codex/memories`、`AGENTS.md` 或高风险生产规则。

## 9. 保真省 Token 与上下文读取治理（2026-05-21）

借鉴点：
- 省 Token 应优先压缩低密度工具输出，而不是压缩用户目标和验收约束。
- 默认先读摘要，再按置信度和风险回退局部原文或完整原文。
- 高风险任务包括安全、权限、支付、数据库迁移、生产故障、协议兼容、签名和性能瓶颈，不能只凭摘要判断。
- 压缩摘要必须保留 `raw_evidence`、`confidence`、`fallback_condition`，否则不可作为交付证据。
- 项目索引应维护入口、测试、禁读目录、高风险区域和已验证时间，减少重复扫仓。
- 上下文预算应按极速、均衡、精确、审计四种模式切换；高风险结论证据必须走审计/原文路径。
- 外部记忆和会话索引工具应先作为 observe 候选，不默认进入 core 依赖，避免召回污染和运维复杂度。

落地点：
- `skills/adk-token-context-governance/SKILL.md`
- `templates/context/tool-output-summary.md`
- `templates/context/raw-evidence-index.md`
- `templates/context/context-budget-profile.md`
- `templates/context/project-map.md`
- `docs/runbooks/token-context-governance.md`
- `scripts/check-token-budget.sh`
- `tests/test_token_context_governance.sh`

有意排除：
- 不对写操作、删除、部署、数据库写入等命令做“压缩后替代审查”。
- 不只保存摘要而丢弃原文入口，避免复盘时证据不可追溯。
- 不把一次性日志、过期项目结构或未经确认的猜测写成长期索引。
