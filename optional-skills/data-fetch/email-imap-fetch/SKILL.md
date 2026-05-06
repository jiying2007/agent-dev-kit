---
name: email-imap-fetch
description: IMAP 邮件获取——从邮箱获取邮件列表和内容
version: 1.0.0
last_updated: 2026-05-06
triggers:
  - "获取邮件"
  - "读取邮箱"
  - "imap fetch"
non_triggers:
  - "发送邮件"
inputs:
  - 邮箱配置（IMAP 服务器、端口、凭证）
outputs:
  - 邮件列表（JSON 格式）
constraints:
  - 凭证必须从环境变量读取
  - 不修改邮箱状态（只读）
---

# IMAP 邮件获取

## Goal
- 通过 IMAP 协议从邮箱获取邮件列表和内容。

## Prerequisites
- 确认 IMAP 配置（服务器、端口、凭证）可用。
- 获取最小上下文：邮箱地址、筛选条件。

## Workflow

1. **check-config**: 验证 IMAP 配置和凭证
2. **dry-run**: 测试连接和认证
3. **fetch**: 获取邮件列表和指定邮件内容

## Quality Gate
- 邮件获取成功
- 凭证从环境变量读取（未硬编码）
- 邮箱状态未被修改（只读操作）

## Evidence Template
```md
- 邮箱: <email>
- 获取数量: N 封
- 获取状态: pass / needs-fix
```

## 健壮性规范

- **输入验证**: 配置项完整性检查
- **重试策略**: 连接失败最多重试 3 次
- **超时控制**: 单次操作不超过 60 秒
- **异常隔离**: 单封邮件获取失败不影响其他
- **日志记录**: 记录获取数量和耗时
