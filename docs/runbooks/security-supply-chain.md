# Security Supply Chain Runbook

## 目标

第三方技能、脚本、提示词或参考资产进入 gdk 前，完成安全与供应链审查。

## 推荐组合

- Agent：`security-compliance-reviewer -> code-review-governor`
- Skill：`gdk-security-supply-chain + gdk-commit-pr-quality-gate`

## 检查项

- 来源：仓库、版本、commit、维护状态。
- 许可证：LICENSE 是否存在，是否允许目标用途。
- 脚本：可执行文件、危险命令、网络访问、写入范围。
- 敏感信息：token、secret、password、private key、个人路径。
- 安装范围：`core`、`optional`、`profile` 或 `reject`。
- 回滚：如何从 `~/.codex` 移除并恢复上一版本。

## 命令模板

```bash
rg -n "api[_-]?key|token|secret|password|PRIVATE KEY" <candidate_path>
find <candidate_path> -type f -perm -111
bash scripts/devkit.sh validate --strict
```

## 验收门禁

- 未知许可证不得进入 `core`。
- 明文凭证风险未处理不得安装。
- 可执行脚本必须有用途说明和验证证据。
