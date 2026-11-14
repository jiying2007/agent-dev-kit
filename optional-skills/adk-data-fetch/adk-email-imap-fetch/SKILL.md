---
name: adk-email-imap-fetch
description: "用于已授权邮箱的只读 IMAP 邮件列表及正文提取，并限制凭据与输出范围；不用于邮件发送、归档写入或扫描无关邮箱。"
version: 1.0.2
last_updated: 2026-11-14
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
3. **fetch**: 对明确邮箱和 UID 范围使用只读 `EXAMINE` / `UID FETCH BODY.PEEK[...]` 或经证明不置 `\\Seen` 的等价接口；先只读 headers/列表，确需正文时才按 UID 提取，禁止 STORE/COPY/MOVE/EXPUNGE。

## Quality Gate
- 邮件获取成功
- 凭证从环境变量读取（未硬编码）
- 邮箱状态未被修改（只读操作），包括未意外设置 `\\Seen` 或触发服务器端规则；无法验证则标 `not-verified`，不声称 pass。

## Evidence Template
```md
- 邮箱: <email>
- 获取数量: N 封
- 获取状态: pass / needs-fix
```

## 健壮性规范

- **输入验证**: 配置项完整性检查
- **重试策略**: 只对瞬时网络错误按预算有界重试；认证失败/锁定风险不得自动重复。
- **超时控制**: 单次操作不超过 60 秒
- **异常隔离**: 单封邮件获取失败不影响其他
- **日志记录**: 仅记录脱敏账号标识、目标 mailbox/UID 范围、数量和耗时；不可记录明文凭证、认证头或私密正文。
