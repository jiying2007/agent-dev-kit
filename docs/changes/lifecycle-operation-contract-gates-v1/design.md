# 设计说明：lifecycle-operation-contract-gates-v1

## 架构影响

不新增 skill，不变更路由。`adk-interface-contract-design` 在适用时生成生命周期操作基线；`adk-code-review-loop` 将改变该基线的 finding 分流为 `design-change`；`adk-verification-before-completion` 要求记录契约、owner、终止路径和真实环境验证边界。

## 数据与配置影响

新增一份按需读取的 Markdown reference，不新增 schema、运行时配置、外部工具或权限。

## 兼容性与迁移方案

只增加输出字段和失败条件。既有交付物可将生命周期操作标记为 `not_applicable`；不改变已有调用、触发词或 manifest。

## 验证策略

- `tests/test_skill_sop_quality.sh` 固定三个 skill 的生命周期契约关键文本。
- `scripts/devkit.sh validate --quick` 校验资产结构。
- `scripts/devkit.sh validate --strict` 校验 manifest、资产与引用闭包；解释器告警只作为开发环境边界，不冒充 release 证据。
