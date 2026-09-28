# 设计

`receipt()` 生成的 `observed_at` 固定为 `2026-08-29T12:00:00Z`，`emit()` 已显式使用固定 `AS_OF`。直接调用 `validate_receipt()` 的测试却使用系统时间，跨过合同的 30 天窗口后被正确拒绝。

测试模块对直接校验统一注入既有 `AS_OF`；另调用生产函数并指定窗口外时间，证明过期拒绝仍生效。这样只改变测试输入，不依赖修改主机时钟，也不更改生产合同。

受保护 PR 要求 source SemVer 高于 main 的 7.12.3，因此用 canonical `versioning sync-identity` 前移至 7.12.4。回退时以 main `9dc8c679…` 为源码锚点；不得复用失败的 7.12.3 推广结果。
