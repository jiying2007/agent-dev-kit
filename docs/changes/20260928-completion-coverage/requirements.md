# 完成前命令证据覆盖审计

## 目标与边界

把 `adk-verification-before-completion` 已声明的 Completion Guard Payload 做成可复跑的静态覆盖核对：同一源码快照、必需检查集合、命令结果、新鲜度和遗漏项必须一致。该审计只读取调用方提供的结构化回执，不运行 build/test、验证签名、认证 verifier 或授予完成/发布权限。

## 输入合同

- 顶层必须有固定 schema、`source_snapshot_sha256`、`required_checks`、`observations`、`as_of`、`freshness_seconds`；拒绝未知字段、重复 ID 和空必需集合。
- `passed/failed` 观察项必须带命令、退出码、`ref:<sha256>` 证据、带时区的时间戳、verifier 声明与同源快照摘要。退出码与状态必须一致；未来或过期证据不得算新鲜。
- `skipped` 必须有非空理由；必需项跳过仍是未完成。任何已执行但失败的检查均保留为失败，不因其未列入必需集合而隐藏。

## 输出与验收

报告区分 required、covered、missing、failed、skipped、stale、additional，并绑定输入摘要。`status=pass` 只说明**自报数据的结构和覆盖**，必须同时声明 `completion_allowed=false`、`evidence_authenticated=false`、`verifier_authenticated=false`。缺失、失败、过期、来源不一致的确定性负例均应失败；Python 3.8 原生运行。

依据：[OpenSpec 验证范围披露](https://github.com/Fission-AI/OpenSpec/releases)和[OpenAI Agents SDK 测试边界](https://openai.github.io/openai-agents-python/testing/)；只吸收可验证的范围披露，不复制外部运行时。
