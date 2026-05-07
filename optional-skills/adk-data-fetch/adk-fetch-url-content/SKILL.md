---
name: adk-fetch-url-content
description: URL 正文提取——从网页提取结构化内容
version: 1.0.0
last_updated: 2026-05-06
triggers:
  - "获取网页内容"
  - "抓取链接正文"
  - "fetch url"
non_triggers:
  - "搜索网页"
inputs:
  - URL 地址
outputs:
  - 结构化正文内容（Markdown）
constraints:
  - 必须先检查 robots.txt
  - 不抓取需要登录的页面
---

# URL 正文提取

## Goal
- 从网页 URL 提取结构化正文内容，转为 Markdown 格式。

## Prerequisites
- 确认 URL 格式正确且可达。
- 获取最小上下文：目标 URL。

## Workflow

1. **check-config**: 验证 URL 格式和可达性
2. **dry-run**: 检查 robots.txt 和页面类型
3. **fetch**: 提取正文内容并转为 Markdown

## Quality Gate
- 正文内容已成功提取
- 输出为结构化 Markdown
- 遵守 robots.txt 规则

## Evidence Template
```md
- URL: <url>
- 提取状态: pass / needs-fix
- 内容大小: <size> bytes
```

## 健壮性规范

- **输入验证**: URL 格式校验（http/https）
- **重试策略**: 网络错误最多重试 3 次
- **超时控制**: 单页抓取不超过 30 秒
- **异常隔离**: 抓取失败不阻塞后续流程
- **日志记录**: 记录 URL、状态码、内容大小
