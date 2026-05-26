# Security Supply Chain Runbook

## 目标

第三方技能、脚本、提示词或参考资产进入 adk 前，完成安全与供应链审查。

## 推荐组合

- Agent：`security-compliance-reviewer -> code-review-governor`
- Skill：`adk-security-supply-chain + adk-commit-pr-quality-gate`

## 检查项

- 来源：仓库、版本、commit、维护状态。
- 许可证：LICENSE 是否存在，是否允许目标用途。
- 脚本：可执行文件、危险命令、网络访问、写入范围。
- 敏感信息：token、secret、password、private key、个人路径。
- 运行态：provider/base URL、MCP server、hooks、sandbox、approval policy。
- 工具调用：高风险 tool-call 必须有 allow/deny policy 和拒绝样例。
- 破坏性、外发、支付、删除、权限扩大或生产写入类 tool call 必须有 deterministic allow/deny 或 approval gate；自动生成的守卫规则必须经人工审核和测试证据后才能放行。
- 安装范围：`core`、`optional`、`profile` 或 `reject`。
- 回滚：如何从目标运行时移除并恢复上一版本。
- 文章或教程中的安装命令、代码片段和 GitHub 项目名只能作为候选线索；完成上述检查前保持 `report-only`。
- 外部 Skill 市场、MCP 推荐清单和插件合集不得按热度直接安装；必须逐项审查用途、权限、owner、license、版本锚点和禁用路径。
- 私有 Skill registry 或团队 namespace 不等于可信来源。必须额外审查认证方式、访问范围、上传审核、恶意脚本扫描、版本不可变性、下线/禁用路径和谁有发布权限。
- Codex/Hermes/Claude/OpenCode 类 plugin 或 Skill 包如果包含 hooks、MCP server、app integration、marketplace catalog 或 lifecycle scripts，必须逐项拆开审查；安装包可信不代表每个组件都可启用。
- 安全研究、逆向、抓取、动态 Hook、浏览器自动化、CDP 断点、反混淆和重放验证类资产默认高风险；必须先确认授权范围、目标域名、数据留存、速率限制、敏感信息脱敏和人工兜底流程。
- GUI/Computer Use/桌面或移动端自动化默认高风险；启用前必须使用低权限隔离账户、显式应用白名单，拒绝系统设置、终端、钥匙串/凭据库等敏感应用，并对删除、系统快捷键、外发和支付类动作保留人工确认。
- 对抗性目标、绕过风控、未授权数据提取、Cookie/账号复用、支付/身份/生产系统探测等场景不得通过通用 Skill 自动化执行。
- 外部 AGENTS/CLAUDE/GEMINI 配置分享中的 MCP server、provider relay、API key、hook、命令行安装片段和平台协作命令默认属于运行态连接器候选；只能登记为 report-only，不能复制到 `manifest.yaml`、profile 或目标运行目录。
- 团队协作类 Skill 若涉及共享记忆、权限、消息网关、多平台适配或多人写入，必须单独审查 memory scope、access control、adapter parity、audit log、禁用路径和 rollback。未证明隔离、权限和跨平台输出一致性前，不得进入默认 profile。
- 外部记忆后端、跨工具会话索引、LLM wiki、MCP memory provider、embedding 服务和数据库适配层默认按运行态连接器审查。必须声明数据驻留位置、凭据来源、namespace 隔离、写入权限、备份/回滚、日志脱敏、删除能力和禁用路径；未完成前只能作为 `report-only` 架构参考。
- 会写入用户目录、重建运行时目录、创建符号链接投影、安装 marketplace 包、配置消息机器人、开启 cron/hook/web server 或远程命令执行的教程，默认 `reject`，除非另有完整供应链和运行态权限审查。
- AI 工具执行环境默认最小权限、无凭证、可隔离；模型切换、能力升级或长上下文扩容不得降低 sandbox、approval、allow/deny、审计日志和人工确认要求。

## 命令模板

```bash
rg -n "api[_-]?key|token|secret|password|PRIVATE KEY" <candidate_path>
find <candidate_path> -type f -perm -111
rg -n "BASE_URL|base_url|mcp|hook|approval|sandbox" <candidate_path>
bash scripts/devkit.sh validate --strict
```

## 验收门禁

- 未知许可证不得进入 `core`。
- 明文凭证风险未处理不得安装。
- 可执行脚本必须有用途说明和验证证据。
- Skill 内脚本必须说明输入/输出、依赖、cwd/env、可写范围、dry-run 或测试方式；缺少任一项时只能保留为文档候选，不得进入 `core` 或默认 profile。
- MCP/server/API relay 未声明信任边界前不得启用工具调用。
- 高风险工具缺少 `templates/security/tool-call-policy.md` 同类策略时不得进入生产 profile。
- 模型升级或工具守卫生成若缺少本地回归、拒绝样例和 owner 审核证据，不得进入默认 profile。
- 只有营销数据、榜单热度或教程截图，没有版本锚点、许可证和验证证据时，不得进入 `manifest.yaml` 或生产 profile。
- 私有仓库只证明分发范围受控；若缺少管理员审核记录、自动扫描结果或 rollback 证据，不得作为 `global-ready` Skill 安装来源。
- 动态采集类工具必须默认静态优先、低预算、摘要输出和完整证据落盘；只有在授权明确、静态证据不足且人工确认后，才允许升级到动态执行。
