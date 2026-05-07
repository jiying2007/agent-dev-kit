---
name: gdk-data-fetch
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
  - 必须遵循各子技能的安全与隐私约束
  - 凭证必须从环境变量读取
---

# gdk-data-fetch

## Goal
- 提供统一的数据获取入口，按场景自动选择合适的子技能。
- 支持从网页和邮箱两种数据源获取结构化内容。

## Prerequisites
- 已明确数据源类型（URL 或邮箱）。
- 已准备数据源的访问凭证或 URL。

## 子技能

| 子技能 | 触发场景 | 输出格式 |
|--------|----------|----------|
| `gdk-fetch-url-content` | 获取网页正文、抓取链接内容 | Markdown |
| `gdk-email-imap-fetch` | 获取邮件列表、读取邮箱内容 | JSON |

## Workflow

1. **场景判断**：根据输入判断数据源类型（URL 或邮箱）。
2. **路由到子技能**：
   - URL 类请求 → `gdk-fetch-url-content`
   - 邮箱类请求 → `gdk-email-imap-fetch`
3. **执行子技能**：按照子技能的 Workflow 执行。
4. **输出结果**：返回结构化内容。

## 路由规则

```md
[datafetch-routing]
输入包含 URL（http/https）→ gdk-fetch-url-content
输入包含邮箱/IMAP 配置 → gdk-email-imap-fetch
输入不明确 → 询问用户确认数据源类型
```

## Quality Gate
- 数据获取必须成功（子技能通过）。
- 输出必须为结构化格式。
- 凭证未硬编码。
- 遵守数据源的安全规则（如 robots.txt、只读邮箱）。

## Evidence Template
```md
- 数据源类型: url | email
- 子技能: gdk-fetch-url-content | gdk-email-imap-fetch
- 获取状态: pass / needs-fix
- 输出大小: <size> bytes
```

## Failure Handling
- 子技能失败时，记录错误并返回 `needs-fix`。
- 数据源不可达时，提示用户检查网络或配置。
- 凭证缺失时，提示用户设置环境变量。
