# Changes Workspace

此目录用于 `scripts/workflow.sh` 的变更工件管理。

- 活跃变更：`docs/changes/<change-id>/`
- 归档变更：`docs/changes/archive/<YYYYMMDD-change-id>/`

可通过命令创建与维护：

```bash
bash scripts/devkit.sh propose --change <id> --title "说明"
bash scripts/devkit.sh apply --change <id>
bash scripts/devkit.sh verify --change <id>
bash scripts/devkit.sh review --change <id> --result pass --blockers 0 --majors 0 --minors 0
bash scripts/devkit.sh archive --change <id>
```

工件最小要求：
- `proposal.md`：必须含单问题、充分性、Core/Optional、重复性与 breaking change 检查段
- `tasks.md`：必须含 ownership 与并行冲突检查段
- `negative-results.md`：必须含已验证负结果表
