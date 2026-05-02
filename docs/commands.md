# Commands

统一入口：`bash scripts/devkit.sh <command> [options]`

## install

安装 Agent/Skill 到目标工具目录。

```bash
bash scripts/devkit.sh install --tool auto --mode symlink --profile embedded-fullstack
bash scripts/devkit.sh install --tool codex --profile core --with-optional-skill incident-rca-report
bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile personal-core --extra-profile release-hardening --backup --install-report reports/gdk-install-report.md
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

## bridge

执行 `openspec` 与 `global-dev-kit` 的变更工件桥接。  
用于把 `openspec/changes/<change-id>/` 导入到 `docs/changes/<change-id>/`，或反向导出。

```bash
bash scripts/devkit.sh bridge import --change add-dark-mode --openspec-root /repo/openspec
bash scripts/devkit.sh bridge import --change add-dark-mode --from-archive --openspec-root /repo/openspec
bash scripts/devkit.sh bridge export --change add-dark-mode --openspec-root /repo/openspec
bash scripts/devkit.sh bridge export --change add-dark-mode --archive-date 2026-05-02 --openspec-root /repo/openspec
```

## evidence

追加命令级 Evidence Index 记录。

```bash
bash scripts/devkit.sh evidence append --file docs/changes/my-change/negative-results.md --command "bash tests/run_all.sh" --exit-code 0 --summary "all tests passed" --evidence-path docs/changes/my-change/verify-report.md --layer Workflow --artifact verify-report
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

## profile coherence

检查 profile 继承后的增量声明是否存在重复、未知引用或默认 profile 漂移。该检查已纳入 `devkit.sh test`。

```bash
bash scripts/check_profile_coherence.sh
```

## install_assets.sh 扩展参数

- `--list-optional-skills`：列出所有可选技能
- `--with-optional-skill <name>`：按需叠加可选技能（可重复）
- `--backup`：安装前备份目标 `agents/skills`
- `--backup-dir <path>`：指定备份目录
- `--install-report <path>`：生成安装报告
- `--lock-version <version>`：要求 manifest version 匹配
