# openspec Bridge Runbook

目标：把 `openspec` 的变更工件与 `agent-dev-kit` 的 `workflow.sh` 工件链打通，支持双向迁移并保留最小可追溯信息。

## 适用场景

- 你已有 `openspec/changes/<change-id>/`，希望接入 gdk 的 `verify/review/archive` 门禁。
- 你在 gdk 内完成了变更，希望导出回 openspec（活动变更或归档目录）。

## 前置条件

1. openspec 根目录存在（默认 `./openspec`）。
2. gdk 变更目录存在（默认 `agent-dev-kit/docs/changes`）。
3. `change-id` 为 kebab-case（如 `add-dark-mode`）。

## 1) openspec -> gdk（导入）

```bash
bash scripts/devkit.sh bridge import --change add-dark-mode --openspec-root /repo/openspec
```

行为说明：
- 复制 `proposal.md`、`tasks.md`、`design.md(若缺失则补默认模板)`。
- 复制 `specs/`（若存在）。
- 自动补齐 gdk 必需工件：`checklist.md`、`negative-results.md`。
- 生成 `state.yaml` 与 `history.log`。

阶段映射（默认推断）：
- `openspec/changes/archive/*-<change-id>` -> `archived`
- 活动变更且 `tasks.md` 含 `- [ ]` -> `proposed`
- 活动变更且任务全勾选 -> `applied`

可显式覆盖阶段：

```bash
bash scripts/devkit.sh bridge import --change add-dark-mode --stage verified --openspec-root /repo/openspec
```

## 2) gdk -> openspec（导出）

导出为活动变更：

```bash
bash scripts/devkit.sh bridge export --change add-dark-mode --openspec-root /repo/openspec
```

导出为归档变更：

```bash
bash scripts/devkit.sh bridge export --change add-dark-mode --archive-date 2026-05-02 --openspec-root /repo/openspec
```

行为说明：
- 复制 `proposal.md`、`design.md`、`tasks.md`。
- 若存在 `specs/`、`verify-report.md`、`review-report.md` 则一并复制。
- 生成 `.openspec-bridge.yaml`，记录导出时间与 gdk 阶段。

## 3) 常见失败与处理

1. 目标目录已存在
- 处理：更换 `change-id` 或手动清理目标目录后重试。

2. openspec 变更缺少 `proposal.md`/`tasks.md`
- 处理：先补齐最小工件，再执行导入。

3. 阶段不符合预期
- 处理：导入时显式传 `--stage` 覆盖自动推断。

## 4) 导入后建议动作

1. 在 gdk 侧补齐 `proposal.md` 中单问题、边界与 breaking change 检查项。
2. 执行：

```bash
bash scripts/workflow.sh verify --change <change-id>
bash scripts/workflow.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

3. 若通过，再进入 `archive` 阶段。
