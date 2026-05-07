# Reference Adoption Matrix

本文件记录“参考仓库可借鉴内容”在 `agent-dev-kit` 的落地情况，仅保留已本地化、可执行、可验证的能力。

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
- `scripts/openspec_bridge.sh`（openspec `changes/` 与 gdk `docs/changes/` 双向桥接）
- `docs/workflows.md`、`docs/changes/README.md`
- `docs/runbooks/openspec-bridge.md`

## 5. 不纳入项（有意排除）

- 外部仓库特定工具链、命令约定、路径约束。
- 与本仓库目标冲突或不可本地验证的规则。
- 会引入外部依赖耦合的流程要求。

## 6. 参考源 E（产物标签与门禁协同）

借鉴点：
- 交付物必须带标签与状态，避免跨角色交接歧义
- 门禁结论必须与测试/评审证据一致

落地点：
- `optional-skills/adk-artifact-gated-lite/SKILL.md`
- `docs/runbooks/artifact-gated-delivery.md`
- `manifest.yaml`（`adk-artifact-gated-lite` profile + optional skill）

结论：`agent-dev-kit` 保留“规则思想”，但全部转换为本仓库可执行脚本、模板和测试门禁，确保离线独立可用。
