# Proposal: Runtime Profile Health and Compatibility Cleanup

## 问题陈述（单问题）

Codex live health used the default build tree to classify assets even when the live state declared `team-collab`. This made managed profile assets appear unmanaged. An ignored Superpowers vendor directory could also survive source builds and remain in the live runtime despite the ADK forbidden footprint policy.

## 上下文充分性检查

- 已读取 live profile、managed-files、source build、dry-run plan 与 footprint failures。
- 已确认 lock/evidence 文件存在用户进行中的改动，不把它们纳入本次写入范围。

## Core/Optional 边界检查

- profile ownership、build filtering 和 live health 是 core runtime contract。
- Superpowers 只作为参考 provenance，不是 optional runtime capability。

## 变更重复性检查

- 本变更补足既有 remove-external-runtime-compat 未覆盖的 profile-aware live inventory 与 unmanaged retired path 删除语义。

## Breaking Change 检查

- runtime 行为变化仅为移除已声明禁止的 Superpowers vendor 路径；回滚只能走 plan backup。

## Spec 链路检查

- 需求、设计、任务、负结果和验证报告位于同一 change 目录，运行态协议以 managed-files 和 source-to-live plan 为准。

## 安装范围与依赖边界

- 仅 `~/codex -> ~/.codex` 受控链有写入；不添加依赖、不启用新 runtime target。

## Prompt 回归证据计划

- 不修改 prompt、routing text 或模型配置；prompt regression not applicable。

## 收敛模式与退出条件

- runtime health、footprint、routing、target checks 均通过时收敛；lock/evidence 等待现有 ADK worktree clean commit 后拆分处理。

## Proposed Change

- Use the live managed-files inventory for unmanaged-asset classification and fail closed when active profile metadata is malformed or inconsistent.
- Exclude inactive and malformed empty vendor plugins from builds.
- Declare the retired Superpowers live path so `--prune-stale` creates a backup-bound delete action rather than requiring manual deletion.

## Scope and Approval

- Source changes are limited to `~/codex` asset tooling, policy manifest and deterministic tests.
- Live mutation is limited to the reviewed source-to-live plan; it requires explicit approval and rollback backup.
- Lock synchronization and release evidence remain deferred until the existing ADK worktree changes are clean and commit-bound.
