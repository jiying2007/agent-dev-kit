# Legacy Changes Compatibility Notice

此目录不是当前变更工件的写入位置。canonical workspace 已统一为：

- 活跃变更：`docs/changes/<change-id>/`
- 归档变更：`docs/changes/archive/<YYYYMMDD-change-id>/`
- 合同检查：`scripts/check-change-governance.sh`
- 状态机入口：`scripts/devkit.sh propose|apply|verify|review|archive`

请勿在根 `changes/` 下创建新的 `request_analysis/`、`coding/`、`ci_result/` 等平行结构。它们来自 2026-05 的早期 Harness 分析，已被当前 proposal/design/tasks/checklist/negative-results/verify/review 工件取代。

## 迁移命令

```bash
bash scripts/devkit.sh propose --change <change-id> --title "说明" --owner <owner>
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
bash scripts/devkit.sh archive --change <change-id>
```

旧调用 `bash scripts/quality-gates.sh <change-dir>` 仍可运行，但只会显示弃用提示并转发到 `scripts/check-change-governance.sh`。新自动化应直接调用 canonical checker。

完整工件要求见 [`docs/changes/README.md`](../docs/changes/README.md)，Harness 决策见 [`docs/harness-engineering-analysis.md`](../docs/harness-engineering-analysis.md)。
