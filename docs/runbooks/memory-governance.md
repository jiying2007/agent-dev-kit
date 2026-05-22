# Memory Governance Runbook

## 目标

Agent 记忆只保存可复用经验，不保存噪声。任务结束后先做 After Action Review，再生成可审查的 memory candidate；是否写入长期位置由风险、作用域和人工确认决定。

## 四层记忆

| 层级 | 用途 | 默认处理 |
|---|---|---|
| `session` | 当前任务状态、临时 ID、已完成步骤 | 任务结束后通常丢弃或进入 session summary |
| `user` | 稳定偏好和明确授权 | 候选化后等待用户确认 |
| `project` | 项目结构、脚本入口、验证门禁、团队约定 | 优先写项目 runbook 或 `AGENTS.md` 候选 |
| `lesson` | 失败根因、负结果、成功路径和工具限制 | 写入 lessons、archive 或 skill/template 候选 |

不得保存完整聊天记录、临时草稿、过期价格、未经确认推测、密钥、凭据、隐私原文和只对本次任务有用的信息。

## 写入准入

候选必须同时满足：

1. 下次同类任务会用到。
2. 有证据来源，例如命令、文件、错误、验证结果或用户明确要求。
3. 作用域清楚，不能把项目规则误写成全局用户规则。
4. 风险分级清楚，且高风险需要人工确认。
5. 有 `last_verified`；依赖外部 API、路径、平台策略或用户偏好时必须有 `next_review_by`。

## 风险分级

| 风险 | 示例 | 处理 |
|---|---|---|
| 低风险 | 图片要检查重叠、发布前跑指定 dry-run、已证实工具限制 | 可自动生成候选，允许进入审计材料 |
| 中风险 | 项目默认目录、跨团队工作流、默认脚本选择 | 生成候选并说明影响范围和回退位置 |
| 高风险 | 自动发布、删除文件、操作生产数据库、支付动作、保存账号或密钥、扩大权限 | 必须 `requires_user_confirmation: true`，不得自动落地 |

## 写入路由

| write_route | 使用场景 |
|---|---|
| `none` | 不值得保存，只在本次回复说明 |
| `session-summary` | 仅用于会话接力 |
| `project-runbook` | 项目内稳定流程或验证步骤 |
| `project-AGENTS` | 必须影响未来 Agent 默认行为的项目规则 |
| `user-memory` | 用户长期偏好，必须确认 |
| `archive` | 研究结论、复盘材料、证据链 |
| `skill-template` | 可复用为 skill 或模板的流程 |

## stale / 冲突治理

- 外部 API、平台规则、路径和用户偏好不是永久真理，必须设置 `next_review_by`。
- 新候选与旧规则冲突时，使用 `conflicts_with` 标记，不静默覆盖。
- 新规则替代旧规则时，使用 `supersedes` 标记并说明依据。
- 长期未使用或被验证推翻的候选应降权、归档或删除。

## 执行流程

1. 任务完成后用 `templates/memory/after-action-review.md` 复盘。
2. 从复盘中提取 reusable lessons。
3. 对每条 lesson 生成 `templates/memory/memory-candidate.md`。
4. 按风险决定自动记录候选、请求确认或拒绝写入。
5. 修改本治理资产后运行：

```bash
rtk bash scripts/check-memory-governance.sh
rtk bash scripts/validate-assets.sh --strict
```
