# 设计与边界

只更新经过当前实际读取支持的来源日期及采纳解释，沿用 90 天有效期：2026-10-13 至 2027-01-11。日期采用既有 HKT +08 规则；本次读取 UTC 和 HKT 均为 2026-10-13。

保留生产过期拒绝逻辑、权限和 conformance。OpenCode 的 metadata 是官方可选项、ADK 静态导出要求更强；新增 slash/autoinvoke 元数据能力不在本次采纳。Claude skill 描述是官方推荐项，ADK 保留 name/description 的本地可移植约束。

OWASP 指南下载超时，官方发布文章明确列出十项风险，足以复核当前 taxonomy-only 采纳；不声称完整指南复审、控制有效性或安全认证。

回滚：精确回退本 change 的源码提交会恢复过期拒绝状态；不修改原 detached child、root dirty 或 live 资产。

版本决策：现有 README 与发布规则要求每个 main 合并严格推进 SemVer，因此必要范围追加 8.0.5 → 8.0.6 的七项同步投影及 CHANGELOG。补丁仅来源维护，无 API/schema 破坏。campaign_id 同步为 software-m5-8.0.6 是新 source 身份，旧 runtime/scorecard 不能重标到新身份。正式 tag/release 由 successful-main promotion 创建，禁止移动旧 tag。上一发布 v8.0.5 是回退锚点，回退必须重新验证且仍受来源有效期门禁限制。
