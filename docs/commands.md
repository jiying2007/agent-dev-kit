# Commands

统一入口：`bash scripts/devkit.sh <command> [options]`

ADK core 只提供平台中立命令。Direct export 运行时适配必须通过 `manifest.yaml:tool_targets` 显式声明；需要外部声明式链路承接的运行体系进入 `manifest.yaml:external_handoff_targets`，不能把平台专属 handoff 或用户目录写入作为默认路径。

## install

安装 Agent/Skill 到受支持工具目录。

```bash
bash scripts/devkit.sh install --tool auto --mode symlink --profile embedded-fullstack
bash scripts/devkit.sh install --tool claude-code --target /tmp/adk-claude-target --mode copy --profile core --extra-profile release-hardening
```

常用参数：

- `--tool auto|claude-code|hermes-agent|opencode`
- `--mode symlink|copy`
- `--profile <name>`
- `--extra-profile <name>`
- `--with-optional-skill <name>`
- `--target <path>`
- `--backup`
- `--install-report <path>`
- `--lock-version <version>`

## validate

校验 manifest、目录映射、frontmatter、profile 引用、workflow、context layer 和资产质量规则。

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh validate --quick
bash scripts/devkit.sh validate --strict --summary-json
```

## convert

将 profile 资产导出为目标工具格式。

```bash
bash scripts/devkit.sh convert --target claude-code --profile core --out dist/claude-code --clean
bash scripts/devkit.sh convert --target hermes-agent --profile core --extra-profile release-hardening --out dist/hermes-agent --clean
bash scripts/devkit.sh convert --target opencode --profile team-core --with-optional-skill adk-test-flakiness-triage --out dist/opencode --clean
```

`--target` 的取值必须来自 `manifest.yaml:tool_targets`。新增 direct target 前先补 manifest、转换语义、拒绝条件、回滚路径和 runtime-boundary 验证。

Codex 当前不是 direct `tool_targets` 成员，因此不是 `convert --target` 的合法取值；它由 `manifest.yaml:external_handoff_targets.codex` 描述为 `~/codex -> ~/.codex` source-to-live 交付链路。

## runtime-boundary

检查 active runtime surface 是否保持通用 ADK 边界。

```bash
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh runtime-boundary --summary-json
```

该门禁检查：

- core 不声明平台专属默认 target。
- direct `tool_targets` 与 `external_handoff_targets` 不重名、不共用 runtime 语义。
- Codex 支持只能以 non-direct source-to-live handoff 表达，不能隐式进入 direct export target。
- `reference_sources` 只能表示 citation/provenance/governance，不能表示 runtime enablement。
- active 脚本和测试不暴露平台专属 handoff 命令。
- 已下线兼容脚本不会作为 active path 回流。
- 平台名只允许出现在 reference metadata、archive 或负向门禁中。

## token-budget

检查 active Skill 入口、active docs、高信号治理脚本、全量测试输出策略和上下文资产是否符合低 token 预算。

```bash
bash scripts/devkit.sh token-budget
bash scripts/devkit.sh token-budget --summary-json
```

## codify-governance

检查交付后可复用模式沉淀门禁。该命令确认 AAR、完成前验证和 Codify Decision 模板都包含 reusable pattern、do-not-promote、owner review、rollback 和 verification evidence 字段。

```bash
bash scripts/devkit.sh codify-governance
```

## knowledge-compile

检查知识编译三层模型。该命令确认 knowledge compile runbook、note 模板和 token context skill 同步声明 `raw_sources`、`maintained_wiki`、`schema`、`ingest/query/lint` 与 raw fallback 边界。

```bash
bash scripts/devkit.sh knowledge-compile
```

## reuse-before-rebuild

检查新增资产前的复用优先门禁。该命令确认 upstream intake、skill curation、reuse decision 模板和 fixture 都要求先做 `existing_asset_search`，再选择 `use-as-is`、`adapt-existing`、`build-fresh` 或 `reference-only`。

```bash
bash scripts/devkit.sh reuse-before-rebuild
```

## context-experience

检查渐进记忆检索与低 token profile。该命令确认 `search_index -> timeline_context -> observation_details` 只读披露流程、memory search result 模板、low-token profile 模板和安全例外保持一致。

```bash
bash scripts/devkit.sh context-experience
```

## openai-governance

校验 OpenAI 官方 Developers 参考来源、freshness、promotion gate 和平台中立 ADK 契约。该命令治理的是 `reference_sources` 和 promoted contracts，不表示 ADK 绑定 OpenAI runtime。

```bash
bash scripts/devkit.sh openai-governance
bash scripts/devkit.sh openai-governance --summary-json
```

## openai-runtime-capabilities

校验 OpenAI 官方 Codex Developers 内容转化后的运行态能力门禁。该命令聚焦可执行检查，而不是资料登记本身：

- permission profile lint baseline：禁止混用旧 sandbox 配置，要求 deny-read、glob depth、domain deny-wins、Unix socket allowlist 和危险网络默认禁用。
- MCP runtime contract lint：要求 tool allowlist/denylist、timeout、approval mode、OAuth/callback/scope、凭证边界、dry-run/fallback。
- subagent job evidence schema：要求 worker job、CSV fan-out、parent integration decision 和 nested subagent 默认禁用。
- terminology lint baseline：用 Codex glossary 对齐 agent、skill、plugin、automation、worktree、MCP server、permission profile 等术语。

```bash
bash scripts/devkit.sh openai-runtime-capabilities
bash scripts/devkit.sh openai-runtime-capabilities --summary-json
bash scripts/devkit.sh openai-runtime-capabilities --fixture fixtures/openai-runtime-capabilities/pass/permission-safe-profile.json
```

## harness-loop-engineering

检查外部 harness/loop engineering 合同门禁。该命令确认 repo-task eval、CI gate、durable loop、coding agent loop、trace observability 和 guardrail handoff 只作为 method-only 证据吸收，不启用外部 runtime、hook、daemon 或自动写操作。

新增或调整合同 fixture 时，先按 `templates/governance/contract-fixture.md` 填写 source mapping、positive fixture、negative fixture 和 rollback path，再按 `docs/runbooks/contract-fixture-authoring.md` 更新 manifest 与 checker。

```bash
bash scripts/devkit.sh harness-loop-engineering
bash scripts/devkit.sh harness-loop-engineering --summary-json
```

## workflow-closure

检查 workflow 引用的 agent/skill 是否都在目标 profile 闭包内。

```bash
bash scripts/devkit.sh workflow-closure --profile core
bash scripts/devkit.sh workflow-closure --profile personal-core --extra-profile release-hardening --summary-json
```

## goal

检查 ADK 目标契约，确认目标、非目标、验收证据、workflow、性能预算和维护责任都能解析到当前资产。

```bash
bash scripts/devkit.sh goal check
bash scripts/devkit.sh goal check --summary-json
```

## capability

检查 ADK 功能健康闭环，确认 goal -> agent -> skill -> workflow -> script -> test -> doc 引用完整。

```bash
bash scripts/devkit.sh capability health
bash scripts/devkit.sh capability health --summary-json
```

## file-modes

检查 tracked 文件权限是否匹配 Git index。规则是 `100644` 不可执行，`100755` 可执行；文档、README、manifest、skill、template 默认不应带 executable bit。

```bash
bash scripts/devkit.sh file-modes
bash scripts/devkit.sh file-modes --fix
```

该检查已纳入 `bash scripts/devkit.sh test`。

## asset-taxonomy

检查 Skill/Optional Skill 分类元数据、Workflow 类型与入口/退出证据、Profile include 顺序和 `skill_routing_matrix` 引用完整性。

```bash
bash scripts/devkit.sh asset-taxonomy
```

该检查会阻止：

- skill 缺少 `category`、`lifecycle_order`、`stage_order`、`activation_mode` 或 `pattern`。
- workflow 缺少 `workflow_type`、`lifecycle_order`、`entry_conditions` 或 `exit_evidence`。
- manifest 中 `skills`、`optional_skills` 或 `workflows` 的物理顺序偏离生命周期或阶段顺序。
- profile 的 `include_skills` 顺序偏离生命周期或阶段顺序。
- routing matrix 引用不存在的 skill、workflow 或 profile。

## catalog

生成或检索 Agent/Skill/Workflow/Profile 目录索引。
生成结果包含 `Agent Contract Matrix`、按 taxonomy 排序的 `Skills`、`Workflows`、`Workflow Matrix` 和 `Skill Routing Matrix` 章节，用于审查 Agent ownership、profile、command risk、primary agent、primary skill、supporting/fallback skills、entry/exit evidence 和 verification 的关系。默认输出到 `docs/agent-skill-catalog.md` 时，会同步生成 `docs/workflow-contract-matrix.md` 和 `docs/reference/skill-routing-matrix.md`。

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh catalog find --type skill --keyword bring-up
bash scripts/devkit.sh catalog find --type optional-skill --keyword 事故
bash scripts/devkit.sh catalog find --type workflow --keyword 完成前验证
```

## match

根据输入文本判断是否命中 skill 触发条件，优先过滤 `non_triggers`。

```bash
bash scripts/devkit.sh match --skill adk-requirements-triage --text "收到模糊需求或跨团队需求时"
bash scripts/devkit.sh match --skill adk-incident-rca-report --scope optional-skill --text "出现线上故障且需要复盘闭环"
```

## bridge

执行 spec 工件与 agent-dev-kit 的变更工件桥接。用于把外部 spec change 目录导入到 `docs/changes/<change-id>/`，或反向导出。

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

按 blocker/major/minor 分级评审并写入 `review-report.md`。仅在 `verified` 状态可执行。

```bash
bash scripts/devkit.sh review --change my-change --result pass --blockers 0 --majors 0 --minors 2
```

## archive

将已评审通过变更归档到 `docs/changes/archive/<date>-<change-id>`。默认要求状态为 `review-passed`，否则失败。

```bash
bash scripts/devkit.sh archive --change my-change
```

## test

执行全量回归测试。默认输出为紧凑模式；失败时只展开有界日志。需要完整子测试日志时使用 `--verbose`。

```bash
bash scripts/devkit.sh test
bash scripts/devkit.sh test --verbose
bash scripts/devkit.sh test --fail-fast
```

## health

检查仓库结构、依赖、配置、测试和质量门禁的健康状态。

```bash
bash scripts/devkit.sh health
```

## backup

执行备份、恢复、列表和回滚相关操作。真实恢复或覆盖前必须确认目标路径、备份内容和回滚影响。

```bash
bash scripts/devkit.sh backup list
```

## ops

执行日常、周常或月常运维编排。自动化默认 report-only，写操作必须显式传 `--apply`。

```bash
bash scripts/devkit.sh ops weekly --summary-json
bash scripts/devkit.sh ops cleanup --apply
```

## monitor

执行系统监控与告警检查。

```bash
bash scripts/devkit.sh monitor
```

## perf

执行性能分析与优化检查。`analyze` 和 `benchmark` 支持低 token JSON 摘要；`benchmark` 默认只跑轻量 validate smoke，显式传 `--include-quick-tests`、`--include-quality` 或 `--include-io` 才扩大测量面；`report` 默认输出到 stdout，只有 `--out` 才写文件。

```bash
bash scripts/devkit.sh perf analyze --summary-json
bash scripts/devkit.sh perf benchmark --summary-json
bash scripts/devkit.sh perf budget --summary-json
bash scripts/devkit.sh perf budget --strict --timing-json /tmp/adk-run-all-quick.json
bash scripts/devkit.sh perf report --out /tmp/adk-performance-report.md
```

## perf-budget

性能预算契约的直达入口，等价于 `bash scripts/devkit.sh perf budget`，用于脚本化门禁中减少一层子命令分发。

```bash
bash scripts/devkit.sh perf-budget --summary-json
bash scripts/devkit.sh perf-budget --strict --timing-json /tmp/adk-run-all-quick.json
```

## security

执行安全扫描与加固检查。

```bash
bash scripts/devkit.sh security
```

## release

执行发布准备、验证、构建、发布或回滚相关流程。

```bash
bash scripts/devkit.sh release check
```

## version

执行版本查看、锁定、升级、对比或 changelog 生成。

```bash
bash scripts/devkit.sh version show
bash scripts/devkit.sh version changelog --version 2.9.1
```
