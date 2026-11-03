---
name: adk-data-fetch
description: 数据获取技能组合——包含邮件获取与网页正文提取
version: 1.0.0
last_updated: 2026-05-06
triggers:
  - "获取数据"
  - "数据抓取"
  - "fetch data"
non_triggers:
  - 数据处理与分析（应使用其他技能）
  - 数据库操作
inputs:
  - 数据源描述（URL 或邮箱配置）
outputs:
  - 结构化内容（Markdown 或 JSON）
constraints:
  - 必须显式安装所需子 Skill；父 Skill 不自动安装子 Skill，缺失时停止并提示安装
  - 凭证必须从环境变量读取
---

# adk-data-fetch

## Goal
- 提供统一的数据获取入口，按场景自动选择合适的子技能。
- 支持从网页和邮箱两种数据源获取结构化内容。

## Prerequisites
- 已明确数据源类型（URL 或邮箱）。
- 已准备数据源的访问凭证或 URL。
- 已确认目标运行时**单独安装**对应的 `adk-fetch-url-content` 或 `adk-email-imap-fetch`；父 Skill 不会隐式安装它们。

## 子技能

| 子技能 | 触发场景 | 输出格式 |
|--------|----------|----------|
| `adk-fetch-url-content` | 获取网页正文、抓取链接内容 | Markdown |
| `adk-email-imap-fetch` | 获取邮件列表、读取邮箱内容 | JSON |

## Workflow

1. **场景判断**：根据输入判断数据源类型（URL 或邮箱）。
2. **路由到子技能**：
   - URL 类请求 → `adk-fetch-url-content`
   - 邮箱类请求 → `adk-email-imap-fetch`
3. **存在性门禁**：检查所选子 Skill 是否存在于已安装的目标目录中；缺失时报告 `needs-fix` 和安装要求，**禁止假定会自动安装或直接执行**。
4. **执行子技能**：仅在子 Skill 实际可用时按照它的 Workflow 执行。
5. **输出结果**：返回结构化内容。

## 路由规则

```md
[datafetch-routing]
输入包含 URL（http/https）→ adk-fetch-url-content
输入包含邮箱/IMAP 配置 → adk-email-imap-fetch
输入不明确 → 询问用户确认数据源类型
```

## Quality Gate
- 数据获取必须成功（子技能通过）。
- 输出必须为结构化格式。
- 缺少子 Skill 时必须停止，不得伪称数据获取成功。
- 凭证未硬编码。
- 遵守数据源的安全规则（如 robots.txt、只读邮箱）。

## Evidence Template
```md
- 数据源类型: url | email
- 子技能: adk-fetch-url-content | adk-email-imap-fetch
- 获取状态: pass / needs-fix
- 输出大小: <size> bytes
```

## 安装边界

`adk-data-fetch`、`adk-email-imap-fetch`、`adk-fetch-url-content` 是三个独立可选安装项。根据实际数据源显式选父 Skill 与**所需**子 Skill；无需 IMAP 时不得因安装父 Skill 隐式扩大邮件权限。首次部署请通过 `adk install plan --with-optional-skill ...` 审核精确目标清单；所有安装都必须遵守现有 plan/apply 授权。

## Failure Handling
- 子技能失败时，记录错误并返回 `needs-fix`。
- 数据源不可达时，提示用户检查网络或配置。
- 凭证缺失时，提示用户设置环境变量。
