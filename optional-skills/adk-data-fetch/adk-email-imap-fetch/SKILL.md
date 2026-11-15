---
name: adk-email-imap-fetch
description: "用于已授权邮箱的只读 IMAP 邮件列表及正文提取，并限制凭据与输出范围；不用于邮件发送、归档写入或扫描无关邮箱。"
version: 1.0.3
last_updated: 2026-11-15
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

1. **check-config**: 验证 IMAP 配置和环境变量凭证；把用户条件落实为明确 mailbox、日期/发件人等筛选、最大封数与字节预算，不默认扫描所有邮箱。
2. **dry-run**: 验证安全连接和认证；`EXAMINE` 指定 mailbox 并核只读状态，保存 UIDVALIDITY。邮箱名、UIDVALIDITY、UID 共同标识邮件，跨会话不能只复用 UID。
3. **fetch**: 用 UID SEARCH 获取候选，按预算分批只读 headers/大小；确需正文时对选定 UID 使用 `UID FETCH BODY.PEEK[...]` 或经证明不置 `\Seen` 的等价接口，禁止 STORE/COPY/MOVE/EXPUNGE。重连先核 UIDVALIDITY；变化时重新查询，不沿用旧游标。
4. **decode**: 按 MIME、传输编码和字符集解析主题/正文，区分 plain text、HTML 与附件；附件不默认下载。列表后被删除、单封超时或解码失败分别记录，保留已经取得的成功项。
5. **deliver**: 输出 JSON 邮件列表，含邮箱引用、UIDVALIDITY、UID、必要 headers、正文状态和逐项错误；说明数量/字节限制及未获取部分。只有所请求范围完整取得才记 pass，局部结果记 partial，不把缺失邮件或正文当空内容成功。

## Quality Gate
- 邮件获取成功
- 凭证从环境变量读取（未硬编码）
- 邮箱状态未被修改（只读操作），包括未意外设置 `\Seen` 或触发服务器端规则；无法验证则标 `not-verified`，不声称 pass。身份/只读语义参考：https://www.rfc-editor.org/rfc/rfc9051.html 。

## Evidence Template
```md
- 邮箱: <email>
- 获取数量: N 封
- 获取状态: pass / partial / needs-fix / not-verified + 未获取原因
- Mailbox / UIDVALIDITY / UID 范围 / 数量与字节限制:
```

## 健壮性规范

- **输入验证**: 配置项完整性检查
- **重试策略**: 只对瞬时网络错误按预算有界重试；认证失败/锁定风险不得自动重复。
- **超时控制**: 按连接、搜索、分批正文各自预算和停止条件设置，不用固定秒数替代任务范围
- **异常隔离**: 单封邮件获取失败不影响其他
- **日志记录**: 仅记录脱敏账号标识、目标 mailbox/UID 范围、数量和耗时；不可记录明文凭证、认证头或私密正文。
