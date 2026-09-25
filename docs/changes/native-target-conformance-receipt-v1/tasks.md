# Tasks: Native Target Conformance Receipt V1

- [x] T1 固定任意文件 hash、未来时间和单证据复用反例。
- [x] T2 增加 strict receipt schema 与 target contract reference schema。
- [x] T3 实现 receipt path/hash/schema/identity、时间、stage 和 authority loader 验证。
- [x] T4 保持三个现有 target 为 static/not-run。
- [x] T5 增加严格正负 fixture 并运行 target contract 定向测试。
- [x] T6 验证 Claude 2.1.138 CLI 与最小权限执行参数。
- [x] T7 尝试隔离 discovery；配置前置失败后按停止条件终止并清理临时目录。
- [x] T8 在新授权下使用合法 empty MCP record 重试；discovery 无合格输出后按条件停止并清理。
- [x] T9 使用当前用户 HOME 与精确最小权限参数最终复核；runtime 返回 not logged in，费用和 token 为零。
- [ ] T10 在不放宽 user/local settings 边界的前提下解决受限模式认证；完成三个独立 stage 前不得提升 target。
- [x] T11 修复 CR5：增加默认禁用的 native conformance trust policy，production loader 无 verifier 时拒绝 promotion。
- [x] T12 增加 self-hashed synthetic receipt 负例；仅显式 synthetic verifier 用于结构单测。
- [x] T13 外部 signature/CI provenance verifier 的受管注入由 7.3.0 `native_trust.py` + managed registry 完成；真实 native receipt/campaign 仍由 T10 独立约束。
