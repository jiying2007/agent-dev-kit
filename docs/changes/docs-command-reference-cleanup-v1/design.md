# Design

## Scope

本变更只处理“当前可执行入口的文档投影”一致性，不修改历史变更记录、产品版本、路由、release、runtime 或 field evidence。

## Approach

- 修正 README 中已经退役的 maturity test 路径。
- 扩展现有 `tests/test_docs_cli_alignment.sh`，而不是新增平行文档门禁。
- 门禁维护一个显式 active-doc 列表，并执行两类检查：
  1. 文档出现的 `scripts/*.sh` / `tests/*.sh` 路径必须存在；
  2. 显式 retired tokens 不得出现在 active docs。
- `docs/changes/**` 作为历史证据不扫描，避免把历史事实误当 active contract。

## Failure semantics

任一 active doc 引用不存在脚本/测试，或重新引入 retired token，测试 fail closed，并输出具体文档与引用路径。

## Rollback

回滚 README 修正与该测试增强即可；不涉及数据迁移或运行态写入。
