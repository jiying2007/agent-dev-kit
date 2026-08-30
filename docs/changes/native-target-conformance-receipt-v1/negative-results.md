# Negative Results: Native Target Conformance Receipt V1

## 已闭环反例

- README 或任意文件配 matching SHA-256：loader 因非 JSON typed receipt 拒绝。
- discovery/load/trigger 复用 command 或 result digest：loader 拒绝。
- receipt target/runtime/bundle/contract identity 不一致：loader 拒绝。
- receipt 或 contract verification time 在未来：loader 拒绝。
- receipt stage 重叠、乱序、duration 与 timestamp 不一致：loader 拒绝。
- Receipt 使用任意随机 digest，并对 authority body 自算匹配 SHA-256：结构验证可自洽，但 production loader 因未注入 trust verifier 拒绝 promotion。

## Claude 原生 smoke 负结果

- Runtime：Claude Code 2.1.138。
- 隔离目标：临时 `.claude`，core skill-only bundle；结束后已删除。
- 尝试阶段：discovery，模型调用前配置校验。
- 失败：`--mcp-config "{}"` 缺少 `mcpServers` record。
- 处理：首次失败后按条件停止；后续仅在两次独立显式授权下重试合法 empty MCP record。

### Empty MCP record 重试

- 全新隔离 target 安装成功，discovery 进程 exit 1 且无可校验 structured output。
- 最后一次使用当前用户 HOME、project-only settings 和精确最小权限参数直接复核，runtime 明确返回 `Not logged in`。
- 最终复核没有进入 API：duration、input/output token 与费用均为零。
- 未放宽 user/local settings、hooks、MCP 或 tools，未执行 load/trigger，未保留 raw output/session identity，未生成 receipt。
- Claude、OpenCode、Hermes target 均保持 static/not-run；后续仍须三个独立 stage 全部通过。

### CR7 project Skill discovery / auth 交叉复核

- 使用真实 `claude-code` core export，把 `adk-requirements-triage` 放入临时项目 `.claude/skills/`；
  工具、MCP、Chrome、会话持久化均关闭，permission mode 为 plan，单次预算上限 USD 0.03。
- `setting-sources=""`：Claude 明确返回 unknown command，证明禁用 project source 时 Skill 未进入 discovery；
  API duration、Token、费用均为零。
- `setting-sources=project`：项目 source 可用，但 OAuth 未进入非交互会话，返回 not logged in；Token/费用为零。
- `setting-sources=user,project`：仍返回 not logged in；Token/费用为零。`claude auth status` 同一环境虽报告
  OAuth logged-in，但该状态不能作为 `claude -p` 的可用认证证据。
- 三次均未进入模型 API，累计费用仍为 USD 0；未执行 load/trigger、未生成 native receipt、未保存 raw output。
- 临时目录只含导出的公开 ADK assets，不含认证信息、session、模型输出或凭证；R6 继续 `not-run`。
- 停止继续尝试：当前阻塞已收敛为 Claude CLI 非交互 auth/setting-source 耦合，需要 operator 重新登录或提供
  受管 `apiKeyHelper/setup-token` 边界；不得通过放宽 tools、settings、MCP 或凭证隔离绕过。

## Trust boundary

- SHA-256 完整性不是签名或 provenance。
- 当前 trust policy 默认 disabled，production verifier 未配置。
- Synthetic verifier 只存在于单元测试，不得作为 runtime certification evidence。
- 外部 signature/CI provenance end-to-end 验证仍 open。
