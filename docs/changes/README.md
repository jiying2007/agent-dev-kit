# ADK Change Workspace

`docs/changes/` 是 ADK 原生变更治理的唯一权威入口，不与任何外部 spec/workflow 产品维持并行事实源。

## Canonical Change Contract

每个 active change 位于 `docs/changes/<change-id>/`，通过 `proposal.md` 中的 `## Canonical Change Contract` 把以下语义压到同一条可验证追踪链：

`Requirement → ADDED/MODIFIED/REMOVED Delta → Affected Surface → Acceptance → Task → Verification → Evidence`

规则：

- `Requirement ID` 使用 `REQ-NNN`，验收使用 `ACC-NNN`，任务使用 `TASK-NNN`，验证使用 `VERIFY-NNN`。
- Delta operation 只允许 `ADDED`、`MODIFIED`、`REMOVED`。
- Contract 引用的 `TASK-NNN` 必须真实存在于 `tasks.md`。
- `verify-report.md` 必须覆盖 Contract 中声明的 `VERIFY-NNN`，命令级结果继续进入 `negative-results.md` 的 Evidence Index。
- Git 是 implementation truth；Canonical Change Contract 是 semantic truth；Evidence/Promotion 是 verification/release truth。不得复制 Git diff 或 CI 状态形成第二事实源。

## Lifecycle

```text
Intent / Proposal
  → Canonical Change Contract
  → Design
  → Tasks / Implementation
  → Verify / Typed Evidence
  → Review
  → Archive / Provenance
  → repository exact-head promotion evidence（独立权威）
```

统一入口：

```bash
bash scripts/devkit.sh propose --change <id> --title "..."
bash scripts/devkit.sh apply --change <id>
bash scripts/devkit.sh verify --change <id>
bash scripts/devkit.sh review --change <id> --result pass --blockers 0 --majors 0 --minors 0
bash scripts/devkit.sh archive --change <id>
```

归档后的 change 位于 `docs/changes/archive/<YYYYMMDD-change-id>/`，必须携带 `provenance.md`；archive 是不可变历史与来源绑定，不只是目录移动。仓库级发布/晋级仍以 `adk-promotion-evidence/v1` 的 exact-head 证据为权威，不在 change workspace 复制 CI 真相。

## External interoperability boundary

ADK core 不保留 OpenSpec profile、CLI、bridge、目录结构或双向同步契约。外部规范工具的有价值语义应先转换为 ADK Canonical Change Contract。

只有存在具名、活跃的真实 consumer，且 native contract 无法直接消费时，才允许在独立边缘 adapter 中实现互操作；依赖方向必须始终是 `adapter → ADK core`，core 不得依赖 adapter。没有 consumer 就不创建 adapter skeleton。
