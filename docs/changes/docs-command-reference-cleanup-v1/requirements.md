# Requirements

## Goal

收敛 active documentation 与当前 ADK 命令/脚本入口之间的漂移，避免已退役路径继续出现在维护者会直接复制执行的文档中。

## Requirements

1. `README.md` 不得引用已退役的 product maturity v3/v4 测试入口。
2. Active docs 中引用的 `scripts/*.sh` 与 `tests/*.sh` 必须在当前仓库真实存在。
3. Active docs 不得把 `manifest.yaml`、已删除的 Scorecard workflow、v3/v4 maturity test 当作当前入口。
4. Historical `docs/changes/**` 保留审计价值，不纳入机械清洗。
5. 现有 CLI、Manifest、release/runtime/field evidence 语义不得改变。
6. 回归必须进入现有 full test suite，并由 Python 3.11/3.12 CI 验证。
