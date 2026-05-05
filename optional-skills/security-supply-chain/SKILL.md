---
name: security-supply-chain
description: 第三方技能、脚本与参考资产引入前的安全和供应链审查
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "供应链审查"
  - "第三方引入"
  - "安全审查"
non_triggers:
  - 仅读取参考仓库做背景调研
  - 修改本仓已有文档且不引入外部资产
inputs:
  - 候选资产路径、许可证、脚本清单、外部依赖、安装范围
outputs:
  - 安全审查结论、阻塞项、允许范围、回滚要求
constraints:
  - 未知许可证或敏感信息风险未处理前不得进入 core
  - 可执行脚本必须说明用途与验证命令
---

# security-supply-chain

## Goal
- 防止第三方资产未经审查进入 `~/.codex` 生产运行环境。

## Prerequisites
- 已明确候选资产来源、版本或 commit。
- 已明确安装范围：`core`、`optional`、`profile` 或 `reject`。

## Workflow
1. 来源审查：确认仓库可达性、维护状态、版本锚点。
2. 许可证审查：确认 LICENSE 与使用范围。
3. 脚本审查：列出可执行脚本、危险命令、网络访问和写入路径。
4. 敏感信息审查：检查密钥、token、个人路径和内部域名。
5. 安装范围审查：确认仅进入 core/optional/profile 中的最小范围。
6. 回滚审查：给出移除方式和安装回退点。

## Commands
```bash
rg -n "api[_-]?key|token|secret|password|PRIVATE KEY" <candidate_path>
find <candidate_path> -type f -perm -111
bash scripts/devkit.sh validate --strict
```

## Evidence Template
```md
- Source + Version:
- License Decision:
- Executable Scripts:
- External Dependencies:
- Secret Scan:
- Install Scope:
- Rollback Path:
- Final Decision:
```

## Failure Handling
- 存在明文凭证、未知许可证或不可解释脚本时，结论为 `reject` 或 `needs-fix`。

## Quality Gate
- 进入 `core` 前必须完成安全与供应链审查。
- 进入 `optional/profile` 前必须有最小安装范围与回滚路径。
