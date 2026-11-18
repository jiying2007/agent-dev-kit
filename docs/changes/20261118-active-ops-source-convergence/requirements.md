# ADK 11.4.5：活跃只读运维与版本文档去漂移

## 原因
- `scripts/auto-ops.sh` 入口先阻断 `--apply`，却保留约百行只可能在写入模式调用的清理、备份与月报实现；其输出误称“添加 --apply 才会写入”。
- `scripts/backup-rollback.sh` 文本仍宣称 Root 具有对应完整版，但 Root 旧恢复路径将被独立退役。
- `pyproject.toml` 使用被 setuptools >=77 警告弃用的许可证 table；README 与帮助示例暴露旧版迁移说明和旧版本号。

## 不变量
仅在 ADK 内修复，保留 `daily|weekly|monthly|cleanup|optimize|security`、只读维护计划、`--summary-json`、`--apply` fail-closed/exit 2、`--force` 未授权错误和所有原发行/安全门禁；不删除历史证据、不重构协议 schema、不更改 live 安装权限。

## 验收
当前主线升至 11.4.5，所有版本身份锚点一致；定向测试覆盖无副作用和拒绝写入；完整 PR/main 回归、独立审查、不可变发行和 Root 精确消费分别验证。真实模型、Token 和产品资格不因源升级提升。
