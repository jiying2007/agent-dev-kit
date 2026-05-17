# Commands

统一入口：`bash scripts/devkit.sh <command> [options]`

## install

安装 Agent/Skill 到非 Codex 目标工具目录。Codex 链路已硬切换为 `convert -> ~/codex -> ~/.codex`，`install --tool codex` 会直接失败。

```bash
bash scripts/devkit.sh install --tool auto --mode symlink --profile embedded-fullstack
bash scripts/devkit.sh install --tool claude-code --target /tmp/adk-claude-target --mode copy --profile core --with-optional-skill adk-incident-rca-report
bash scripts/devkit.sh convert --target codex --profile personal-core --extra-profile release-hardening --codex-profile team-collab --out ../reports/adk-codex-handoff --clean
```

## validate

校验 manifest、目录映射、frontmatter、profile 引用关系。

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh validate --quick
bash scripts/devkit.sh validate --strict --summary-json
```

## convert

将 profile 资产导出为目标工具格式。

```bash
bash scripts/devkit.sh convert --target claude-code --profile core --out dist --clean
bash scripts/devkit.sh convert --target codex --profile core --with-optional-skill adk-test-flakiness-triage --codex-profile team-collab
```

`target=codex` 输出的是 `~/codex` handoff：`src/codex-home/vendor/...` 源资产树和 `manifest-fragments/*.json`，不是 `~/.codex` 运行目录形态。

## codex-handoff

生成生产推荐 handoff，合并到 `/tmp` 中的 `~/codex` 副本，并运行 `~/codex` 的 build、governance、repo、build 与 skill 元数据检查。

```bash
bash scripts/devkit.sh codex-handoff --codex-root ~/codex
```

## runtime-boundary

检查 adk 是否绕过 `~/codex` 直接写入 `~/.codex`。

```bash
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh runtime-boundary --summary-json
```

## workflow-closure

检查 workflow 引用的 agent/skill 是否都在目标 profile 闭包内。

```bash
bash scripts/devkit.sh workflow-closure --profile core
bash scripts/devkit.sh workflow-closure --profile personal-core --extra-profile release-hardening --summary-json
```

## file-modes

检查 tracked 文件权限是否匹配 Git index。规则是 `100644` 不可执行，`100755` 可执行；文档、README、manifest、skill、template 默认不应带 executable bit。

```bash
bash scripts/devkit.sh file-modes
bash scripts/devkit.sh file-modes --fix
```

该检查已纳入 `bash scripts/devkit.sh test`。

## catalog

生成或检索 Agent/Skill/Profile 目录索引。

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh catalog find --type skill --keyword bring-up
```

## match

根据输入文本判断是否命中 skill 触发条件（优先过滤 `non_triggers`）。

```bash
bash scripts/devkit.sh match --skill adk-requirements-triage --text "收到模糊需求或跨团队需求时"
bash scripts/devkit.sh match --skill adk-incident-rca-report --scope optional-skill --text "出现线上故障且需要复盘闭环"
```

## bridge

执行 `openspec` 与 `agent-dev-kit` 的变更工件桥接。  
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
bash scripts/check-profile-coherence.sh
```

## health

健康检查：结构/依赖/配置/测试/质量全面扫描。

```bash
bash scripts/devkit.sh health
```

## backup

备份/恢复/回滚操作。

```bash
bash scripts/devkit.sh backup create
bash scripts/devkit.sh backup restore --id <backup-id>
bash scripts/devkit.sh backup rollback --id <backup-id>
```

## ops

日常/周常/月常运维编排。

```bash
bash scripts/devkit.sh ops daily
bash scripts/devkit.sh ops weekly
bash scripts/devkit.sh ops monthly
```

## monitor

系统监控与告警。

```bash
bash scripts/devkit.sh monitor status
bash scripts/devkit.sh monitor alert
```

## perf

性能分析与优化。

```bash
bash scripts/devkit.sh perf analyze
bash scripts/devkit.sh perf optimize
```

## security

安全扫描与加固。

```bash
bash scripts/devkit.sh security scan
bash scripts/devkit.sh security harden
```

## release

发布准备/验证/构建/发布/回滚。

```bash
bash scripts/devkit.sh release prepare
bash scripts/devkit.sh release verify
bash scripts/devkit.sh release build
bash scripts/devkit.sh release publish
bash scripts/devkit.sh release rollback
```

## version

版本查看/锁定/升级/对比。

```bash
bash scripts/devkit.sh version show
bash scripts/devkit.sh version lock --target 2.7.0
bash scripts/devkit.sh version upgrade
bash scripts/devkit.sh version diff --from 2.7.0 --to 2.7.0
```

## install_assets.sh 扩展参数

- `--list-optional-skills`：列出所有可选技能
- `--with-optional-skill <name>`：按需叠加可选技能（可重复）
- `--backup`：安装前备份目标 `agents/skills`
- `--backup-dir <path>`：指定备份目录
- `--install-report <path>`：生成安装报告
- `--lock-version <version>`：要求 manifest version 匹配

## production codex handoff

生产交接到 `~/codex` 时，推荐使用 `personal-core + release-hardening`，并叠加长任务、组合治理、供应链、交接四类 optional skills；高风险 artifact 门禁由核心 `adk-artifact-gating` 提供，最终由 `~/codex` apply 到 `~/.codex`。

```bash
bash scripts/devkit.sh convert --target codex --profile personal-core --extra-profile release-hardening --with-optional-skill adk-planning-execution-loop --with-optional-skill adk-skill-composition-governance --with-optional-skill adk-security-supply-chain --with-optional-skill adk-cross-team-handoff --codex-profile team-collab --out ../reports/adk-codex-handoff --clean
bash scripts/devkit.sh codex-handoff --codex-root ~/codex
cd ~/codex && rtk bash scripts/build.sh --profile team-collab
cd ~/codex && rtk bash scripts/apply.sh --profile team-collab --dry-run
```

安装后在 `llm_agent` 根目录运行：

```bash
rtk ../scripts/check-global-codex-health.sh ~/.codex minimal
rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot
```

`~/.codex/AGENTS.md` 不由 adk 安装器覆盖；adk 资产先进入 `~/codex`，配合方式见 `docs/codex-agents-integration.md`。


## check-change-governance

检查变更治理合规性。

```bash
bash scripts/check-change-governance.sh <root>
```

## check-format

检查代码格式规范。

```bash
bash scripts/check-format.sh <root>
```

## check-terminology-consistency

检查术语一致性（如 gdk vs adk 命名）。

```bash
bash scripts/check-terminology-consistency.sh <root>
```

## quality-gate-check

质量门禁检查。

```bash
bash scripts/quality-gate-check.sh <root>
```
