# Commands

统一入口：`bash scripts/devkit.sh <command> [options]`

## install

安装 Agent/Skill 到目标工具目录。

```bash
bash scripts/devkit.sh install --tool auto --mode symlink --profile embedded-fullstack
bash scripts/devkit.sh install --tool codex --profile core --with-optional-skill incident-rca-report
```

## validate

校验 manifest、目录映射、frontmatter、profile 引用关系。

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh validate --quick
```

## convert

将 profile 资产导出为目标工具格式。

```bash
bash scripts/devkit.sh convert --target claude-code --profile core --out dist --clean
bash scripts/devkit.sh convert --target codex --profile core --with-optional-skill test-flakiness-triage
```

## catalog

生成或检索 Agent/Skill/Profile 目录索引。

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh catalog find --type skill --keyword bring-up
```

## match

根据输入文本判断是否命中 skill 触发条件（优先过滤 `non_triggers`）。

```bash
bash scripts/devkit.sh match --skill requirements-triage --text "收到模糊需求或跨团队需求时"
bash scripts/devkit.sh match --skill incident-rca-report --scope optional-skill --text "出现线上故障且需要复盘闭环"
```

## propose

创建变更工件目录与模板：`proposal.md`、`design.md`、`tasks.md`、`checklist.md`、`negative-results.md`。
其中 `proposal.md` 会预置单问题、上下文充分性、Core/Optional 边界、重复性与 breaking change 检查项。

```bash
bash scripts/devkit.sh propose --change my-change --title "说明"
```

## apply

将变更状态更新为 `applied`。

```bash
bash scripts/devkit.sh apply --change my-change
```

## verify

执行验证命令并写入 `verify-report.md`，成功后状态变更为 `verified`。

```bash
bash scripts/devkit.sh verify --change my-change
```

## review

按 blocker/major/minor 分级评审并写入 `review-report.md`。
仅在 `verified` 状态可执行。

```bash
bash scripts/devkit.sh review --change my-change --result pass --blockers 0 --majors 0 --minors 2
```

## archive

将已评审通过变更归档到 `docs/changes/archive/<date>-<change-id>`。
默认要求状态为 `review-passed`，否则失败（可用 `--force` 强制归档）。

```bash
bash scripts/devkit.sh archive --change my-change
```

## test

执行全量回归测试。

```bash
bash scripts/devkit.sh test
```

## install_assets.sh 扩展参数

- `--list-optional-skills`：列出所有可选技能
- `--with-optional-skill <name>`：按需叠加可选技能（可重复）
