# Version Decision Request：ADK Platform Convergence

## Current Facts

- 已发布/已演练基线为 `4.0.0`，其 manifest digest 与当前工作树不同。
- 当前变更包含 breaking surfaces：
  - core Profile 移除嵌入式资产；
  - target contract `v1 → v2`；
  - routing IR、Runtime Control V2、Workflow IR 和新 privacy/evidence contracts。
- `4.1.0` 在现有 Software M5 policy 中是完成 field certification 后的 final version，不能在 R10 未完成时占用。
- 重用 `4.0.0` 版本号重建新内容会破坏不可变 release/provenance，禁止。

## Options

| Option | Decision | Reason |
|---|---|---|
| 继续使用 4.0.0 | reject | 同版本不同内容，破坏 artifact/provenance |
| 升为 4.0.1 | reject | core/target contract 是 breaking change，不符合 patch 语义 |
| 升为 4.1.0 | reject-now | 该版本受 M5 final gate 保留，R10 尚未满足 |
| 新建 5.0.0-rc.1 candidate，field 完成后 5.1.0 final | recommended | 与 breaking scope 和新的 campaign/ledger 边界一致 |

## Owner Decision（2026-08-30）

- 已批准把当前 convergence 变更定义为 `5.0.0-rc.1` 本地 candidate，并创建 ADK 子仓本地提交。
- 4.x append-only campaign/ledger 历史不得改写；新 campaign/ledger policy 必须另建。
- 未批准 push、tag、远端 release 或 source-to-live。
- 本地 build/check 属于候选验证；rehearsal 仅在可验证的 `4.0.0` artifact 存在时执行。

## Current Action

- 将版本同步到 `5.0.0-rc.1`，补齐迁移、版本和候选验证证据，再创建本地 ADK commit。
- 不修改旧 ledger，不操作 tag、remote、release 或 live。
- R6 双运行时 campaign 与 R10 field evidence 未满足前，M5/final gate 继续 fail-closed。
