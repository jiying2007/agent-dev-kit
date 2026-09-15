# Canonical Change Authority

Status: accepted

## Decision

ADK absorbs useful specification-driven change semantics, but does not preserve OpenSpec as a parallel authoring, runtime, compatibility, or authority contract.

ADK 原生 `docs/changes/<change-id>/` workflow 是唯一 canonical change authority。核心变更链必须表达：

`Intent → Requirement → Change Delta → Affected Surface → Acceptance → Task → Verification → Evidence → Review → Provenance`

其中 Delta operation V1 仅允许 `ADDED`、`MODIFIED`、`REMOVED`。

## Invariants

1. ADK 只有一个 canonical change authority。
2. OpenSpec 不是 core dependency、authoring contract、runtime contract 或 source of truth。
3. 外部兼容能力必须由具名、活跃 consumer 驱动；没有 consumer 就不创建 adapter。
4. 依赖方向只能是 `adapter → ADK core`，core 永不依赖 compatibility adapter。
5. Git 保存 implementation truth；Canonical Change Contract 保存 semantic truth；Evidence/Promotion 保存 verification/release truth，三者通过稳定 ID 与 commit/evidence identity 关联，不互相复制。
6. Change archive 必须产生 provenance；仓库级晋级继续使用独立的 `adk-promotion-evidence/v1` exact-head 证据。

## Rejected alternatives

### 保留双向 OpenSpec bridge

拒绝。双向 import/export 会制造第二套生命周期、状态映射和事实源，并把外部产品 surface 重新带入 ADK core。

### 在 ADK 新建 OpenSpec-inspired 子系统

拒绝。现有 change workspace 已具有 propose/apply/verify/review/archive 生命周期，应增强现有 bounded context，而不是复制 proposal/spec/tasks 平台。

### 预先创建空 interoperability adapter

拒绝。无真实 consumer 的兼容代码属于未证明的长期维护面。未来如确有需要，必须单独提案、声明 consumer/owner、测试和 sunset 条件。

## Compatibility ratchet

Core regression 必须防止以下 surface 回流：

- `openspec/` core authoring root；
- OpenSpec profile；
- OpenSpec bridge import/export；
- `/opsx:*` core command/runtime invocation；
- OpenSpec package/CLI 作为 core dependency。

文档中的历史决策和 regression 测试可以提及 OpenSpec；这种提及不构成 runtime compatibility。
