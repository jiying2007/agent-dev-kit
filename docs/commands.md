# Commands

统一入口：`bash scripts/devkit.sh <command> [options]`

解释器入口：

- 未设置 `ADK_PYTHON_BIN` 时按 `python3.12 -> python3.11 -> python3` 选择；这会
  优先复用已安装的受审查解释器。若最终版本低于 3.11，除 `doctor` 外会明确
  标记结果仅供开发，不能作为 release evidence。
- 使用 `ADK_PYTHON_BIN=/reviewed/python3.12` 显式选择解释器。
- 发布、制品或认证前设置 `ADK_REQUIRE_SUPPORTED_PYTHON=1`，旧解释器会在 CLI
  执行前 fail-fast。
- 本机没有受支持解释器时，使用
  `scripts/run-local-ci-parity.sh --python all --mode full`；`doctor` 始终可在
  旧环境运行以输出结构化诊断。

ADK core 只提供平台中立命令。`manifest.json` 是唯一结构化 Manifest SSOT，并由 4.0 Draft 2020-12 JSON Schema 与语义规则共同校验；direct export 适配必须通过 `tool_targets` 和 versioned target contract 显式声明。需要外部声明式链路承接的运行体系进入 `external_handoff_targets`，不能把平台专属 handoff 或用户目录写入作为默认路径。

## install

通过可审查 plan、原子 apply 和 receipt rollback 安装 Agent/Skill。`apply` 只接受 UUID/timestamp/TTL 合法、未过期、manifest/contract digest 未漂移、active receipt SHA256 未变化且无冲突的 `adk-install-plan/v2`；未托管目标冲突会在 plan 阶段阻断。新安装写入 `adk-install-receipt/v3`，记录 target contract digest、逐文件 rendered/source SHA256、mode、asset kind、备份和前序 receipt 完整性；`v1/v2` receipt 仅用于兼容回滚，旧 `v1` plan 明确拒绝。

```bash
bash scripts/devkit.sh install plan --tool claude-code --target /tmp/adk-live --mode copy --profile core --asset-kind skill --output /tmp/adk-plan.json
bash scripts/devkit.sh install apply --plan /tmp/adk-plan.json --lock-timeout 30 --summary-json
bash scripts/devkit.sh install rollback --receipt /tmp/adk-live/.adk-install-receipt.json --lock-timeout 30 --summary-json
```

常用参数：

- `--tool claude-code|opencode`
- `--mode copy`（target contract 为防止越界与语义漂移而拒绝 symlink）
- `--asset-kind agent|skill`
- `--profile <name>`
- `--extra-profile <name>`
- `--with-optional-skill <name>`
- `--target <path>`
- `--output <plan.json>`
- `--ttl-minutes <n>`
- `apply/rollback --lock-timeout <seconds>`：等待同一 target 的 active writer，最大 300 秒。

## validate

校验 manifest、目录映射、frontmatter、profile 引用、workflow、context layer 和资产质量规则。

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh validate --quick
bash scripts/devkit.sh validate --strict --summary-json
```

当前 active surface 只接受 canonical `manifest.json`。历史 Manifest 镜像与一次性迁移工具已退出当前维护入口；历史迁移事实仅保留在版本化 change/archive 证据中。

## manifest

只读检查 canonical `manifest.json` 的 bounded-context composition 治理契约。该命令不写文件、不启用 runtime fragment loading、不创建第二 SSOT；它只读取当前 canonical manifest 与 composition policy，并验证 owner partition -> deterministic compose 后语义与 canonical digest 完全一致。

```bash
bash scripts/devkit.sh manifest composition-check
bash scripts/devkit.sh manifest composition-check --summary-json
```

成功报告包含 canonical source、source/round-trip digest、owner domain count，以及 `runtime_enabled=false`、`writes=false` 和 `composition_generator=null`。任何 policy、owner、canonical source、round-trip 语义或 digest 漂移都会 fail closed 并返回非零。物理 manifest split、fragment loader 和 build-time composition generator 不属于当前产品契约；若未来重新引入，必须作为新的 versioned contract 独立设计，而不是复活隐藏兼容入口。

## doctor

只读检查 manifest、Python 3.11+、固定 PyYAML/jsonschema 版本、runtime 安装与认证、CLI 版本、target 可写性和 writer lock 状态。输出只包含状态，不读取或打印凭证值；解释器或依赖不在发布支持基线时返回失败。

```bash
bash scripts/devkit.sh doctor --summary-json
bash scripts/devkit.sh doctor --require-runtime codex --require-runtime claude --summary-json
bash scripts/devkit.sh doctor --target /tmp/adk-live --summary-json
```

## export

将 profile 资产确定性导出为目标工具格式；同一 manifest 与参数必须产生同一文件集合和 digest。

```bash
bash scripts/devkit.sh export --target claude-code --profile core --out dist --clean --lock-timeout 30
bash scripts/devkit.sh export --target opencode --profile team-core --with-optional-skill adk-test-flakiness-triage --out dist --dry-run --summary-json
```

`--target` 的取值必须来自 `manifest.json:tool_targets`。新增 direct target 前先补 manifest、转换语义、拒绝条件、回滚路径和 runtime-boundary 验证。

Codex 当前不是 direct `tool_targets` 成员，因此不是 `export --target` 的合法取值；它由 `external_handoff_targets.codex` 描述为 `~/codex -> ~/.codex` source-to-live 交付链路。

## target

`target check` 对 contract schema、支持的 asset kind、原生路径、frontmatter、permission profile 和全部 resolved assets 执行静态检查。`target smoke` 会先完成同样的静态检查，再把原生树交给调用者显式提供的 runtime command；未提供 runtime command 时返回 `not-run`/exit 2，不能把 static 或 fixture 结果冒充真实运行时认证。

```bash
bash scripts/devkit.sh target check --all --level static --summary-json
bash scripts/devkit.sh target check --target claude-code --level static --summary-json
bash scripts/devkit.sh target smoke --target claude-code --stage discovery --profile core --asset-kind skill --runtime-command /path/to/read-only-runtime-smoke
```

当前 `claude-code`、`opencode` 均为 `experimental`。真实 runtime smoke 至少分 discovery、load、trigger、permission 四阶段；本地结果记录 `started_at`、`duration_ms`、runtime command SHA256、exit code 和 stdout/stderr digest，runtime/version 与可复核证据摘要必须由外部 campaign 一并留存。

## lock

查看 export/install/rollback/campaign 使用的 target writer lock。工具不会自动清理 stale lock；人工清理必须先读取状态，再提交完全匹配的 lock ID。

```bash
bash scripts/devkit.sh lock status --target /tmp/adk-live --summary-json
bash scripts/devkit.sh lock clear --target /tmp/adk-live --expected-lock-id <lock-id> --summary-json
```

`lock clear` 会拒绝本机仍存活的 owner；本机已退出的 owner 可按精确 lock ID 清理，远端或无法判活的 owner 必须达到 stale 阈值后才允许清理。工具仍要求先审阅 `lock status`，不能把 clear 当作 writer 抢占机制。

## task-cost

根据显式任务类型、风险、变更文件数、项目事实、长任务、shared contract 与外部写入信号生成确定性执行预算 receipt。输出包含 `micro | standard | complex | high-risk` 成本级别、上下文预算、计划/验证强度、归档候选要求和 Skill 使用校验；它不读取凭证，不执行任务，也不把成本估计升级为发布授权。

```bash
bash scripts/devkit.sh task-cost --task "优化上下文门禁" --task-type implementation --risk-level medium --changed-files 8 --project-facts --summary-json
bash scripts/devkit.sh task-cost --task "发布候选" --task-type release --risk-level high --long-task --shared-contract --external-write --skill adk-release-versioning --output /tmp/adk-task-cost.json
```

`--destructive` 会强制提升为 `high-risk`。声明的 Skill 与成本合同不匹配时返回非零；`--output` 只写调用方指定的 JSON 路径。

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

## harness

对任意本地仓库执行确定性、只读的 Harness readiness 证据投影。该命令不执行目标仓代码、不安装 MCP、不调用模型，也不生成加权总分。

七个维度分别输出 `pass|partial|needs-review|blocked|not-applicable`、证据路径、owner、验证时间、阻塞项和下一动作。默认只报告；只有显式 `--gate` 才要求总状态为 `pass`，未就绪时退出 2。

```bash
bash scripts/devkit.sh harness readiness --root /path/to/repo
bash scripts/devkit.sh harness readiness --root /path/to/repo --summary-json
bash scripts/devkit.sh harness readiness --root /path/to/repo --output harness-readiness.md
bash scripts/devkit.sh harness readiness --root /path/to/repo --gate
bash scripts/devkit.sh harness readiness --root /path/to/repo --as-of 2026-07-18 --summary-json
```

目标仓可选在 `.adk/harness-readiness.json` 记录每个维度的 `owner` 与 `last_verified_at`；未来日期和超过合同 freshness 窗口的日期会产生专用 blocker。`--as-of` 仅用于固定可复现的 report-only 评估日期；`--gate` 拒绝显式评估日期并强制使用当天，避免冻结时钟绕过 freshness。

存在 MCP 配置时，完整通过还要求 `tool_and_permission_boundary.permission_boundary` 明确声明 `read_only=true`、`approval_required=true` 和受支持的 `credential_source`。自然语言文档只作为补充证据，否定语境不能使权限边界通过。没有 MCP 配置会得到 `not-applicable`，不是失败；硬编码 MCP 敏感值会得到 `blocked`，报告只显示 JSON key path，不显示值。

维度、扫描预算与脱敏合同见 `manifests/harness_readiness_contracts.json`，吸收决策见 `docs/harness-engineering-analysis.md`。

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

## phase-context

Resolve phase context from semantic selectors in `manifests/phase_context_contract_v2.json`. Phase selection is role-aware and does not read Skill directory paths from `manifest.json`.

```bash
bash scripts/devkit.sh phase-context --domain general --phase review --summary-json
bash scripts/devkit.sh phase-context --domain embedded --phase driver-development --summary-json
bash scripts/devkit.sh phase-context --lifecycle --summary-json
```

## skill-relationships

Resolve typed Skill relationships from `manifests/skill_relationship_contracts_v2.json`. Context prerequisites, evidence prerequisites, handoffs, and delivery precedence are explicit typed edges; `manifest.json` carries no parallel `depends_on` graph.

```bash
bash scripts/devkit.sh skill-relationships --summary-json
bash scripts/devkit.sh skill-relationships --lifecycle --summary-json
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
失败时状态为 `verify-failed`；修复工件后可对同一 change 重试 `verify`，无需篡改
`state.yaml` 或重建 change。

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

## benchmark

测量 manifest 校验、profile 解析、target static check、CLI cold-start、10x export plan、10x filesystem I/O 和 peak allocation 的平台自身性能。该命令不声称测量模型推理、真实目标运行时、并发 writer 或现场性能。

```bash
bash scripts/devkit.sh benchmark run --iterations 10 --output /tmp/adk-benchmark.json --summary-json
bash scripts/devkit.sh benchmark report --input /tmp/adk-benchmark.json --output /tmp/adk-benchmark.md
```

## eval

运行确定性路由评测，或生成/执行 Codex、Claude 的只读真实运行时评测。真实运行时必须显式传 `--execute`；默认只返回执行计划，不产生模型调用费用。baseline 与 ADK 使用同一审批策略；runtime 质量门禁要求综合成功率不低于 0.85、路由准确率不低于 0.90、安全准确率不低于 0.90，且没有 runtime error。

```bash
bash scripts/devkit.sh eval run --suite deterministic --output /tmp/adk-eval.json --summary-json
bash scripts/devkit.sh eval effect --contract manifests/effect_eval_contract.json --output /tmp/adk-effect-eval.json --summary-json
bash scripts/devkit.sh eval run --suite runtime --runtime codex --model gpt-5.5 --condition adk --limit 2 --summary-json
bash scripts/devkit.sh eval run --suite runtime --runtime claude --condition baseline --limit 2 --execute --output /tmp/adk-claude-eval.json
bash scripts/devkit.sh eval compare --baseline /tmp/codex-baseline.json --candidate /tmp/codex-adk.json --output /tmp/codex-comparison.json
bash scripts/devkit.sh eval report --input /tmp/adk-eval.json --output /tmp/adk-eval.md
```

`eval compare` 只在 candidate 达到质量门禁、三个指标都不回退且至少一个指标有可测提升时通过。比较结果同时记录 baseline/candidate 的总耗时、中位数和 nearest-rank P95，但延迟是 `observational-not-gating`：单次模型运行的抖动不能替代重复实验或统计显著性分析。缺少 executable 或认证时结果必须是 `not-run`。

`eval effect` 使用输入/标签分离并锁定 hash 的 24 例 source/test 数据集，分别覆盖 12 个 OOD 与 12 个 adversarial case，评分 route、safety、trace、outcome，并禁用 `routing.intents` 做组件消融。它不把标签传入 matcher/runtime prompt，但标签仍对源码 reviewer 可见，因此不是密码学意义的 blind trial，也不替代 runtime/field evidence。

5.x Software M5 campaign 使用 `manifests/software_m5_eval_contract_v5.json`。正式契约保留 RC7 的 60 个任务、Codex/Claude、baseline/ADK、3 trials、模型、最多一次错误重试和 `$150` 硬预算，但使用独立 5.x campaign identity；RC7 合同只作 append-only provenance，不接收 5.x state/result。

```bash
bash scripts/devkit.sh eval campaign plan --contract manifests/software_m5_eval_contract_v5.json --summary-json
bash scripts/devkit.sh eval campaign run --contract manifests/software_m5_eval_contract_v5.json --state-dir /tmp/adk-m5-campaign --execute --approve-budget-usd 150 --summary-json
bash scripts/devkit.sh eval campaign run --contract manifests/software_m5_eval_contract_v5.json --state-dir /tmp/adk-m5-campaign --execute --approve-budget-usd 150 --resume --summary-json
bash scripts/devkit.sh eval certify --contract manifests/software_m5_eval_contract_v5.json --state-dir /tmp/adk-m5-campaign --output /tmp/adk-m5-certification.json
bash scripts/devkit.sh eval campaign report --input /tmp/adk-m5-certification.json --output /tmp/adk-m5-certification.md
bash scripts/devkit.sh eval repository plan --contract manifests/repository_runtime_eval_contract.json --summary-json
bash scripts/devkit.sh eval repository certify --contract manifests/repository_runtime_eval_contract.json --report /tmp/repository-runtime-report.json --output /tmp/repository-runtime-certification.json --summary-json
```

`eval repository` 只验证平台中立的真实仓库 evidence contract。`plan` 不启动外部 runtime、容器、网络或凭证；`certify` 重算 task/contract digest，并验证完整 result matrix、baseline customization isolation、功能优先安全 oracle、过程质量、redacted trace 与 token/cost 分布。Inspect SWE 等 adapter 保持 optional、disabled-by-default。clean-room task 成功时只返回 `fixture-pass`；只有 task 为 owner-approved real repository、adapter 为 `available` 且 `version_pin` 固定为 SHA-256 digest 时才允许真实 `pass`。`fixture-pass` 不能满足根仓 Software M5 的真实仓库门禁。

`certify` 重新派生 route/safety/status，核验每条 record hash，并要求 success、route、safety、paired bootstrap、P95、token、runtime error 和资源证据门禁全部通过。campaign 通过仍只是软件评测证据，不替代 30 天 field pilot。

## security

执行阻断式安全检查：敏感文件名、疑似凭证内容、仓库外 symlink、world-writable 文件、未固定 SHA 的 GitHub Action 和未固定 digest 的 container action 都会失败。扫描范围包含 tracked 文件与未被 ignore 的 untracked 文件。CI 另用固定版本 Ruff 与 `pip-audit --strict` 执行静态分析和依赖审计；这些外部工具不进入 core runtime。

```bash
bash scripts/devkit.sh security check
bash scripts/devkit.sh security check --summary-json
```

## release

执行发布检查、可复现制品构建、本地升级/回滚演练和显式 backend 发布。`publish` 不配置 backend、制品或 checksum 时必须失败；发布前会重新计算 SHA256 并核对制品名与版本，当前只支持 GitHub CLI backend。

```bash
bash scripts/devkit.sh release check
bash scripts/devkit.sh release build --version 6.0.0 --out dist --summary-json
bash scripts/devkit.sh release runtime-build --version 6.0.0 --profile team-core --out dist --summary-json
bash scripts/devkit.sh release rehearse --previous-artifact /tmp/agent-dev-kit-4.0.0.tar.gz --candidate-artifact dist/agent-dev-kit-6.0.0.tar.gz --output /tmp/adk-release-rehearsal.json
bash scripts/devkit.sh release publish --version 6.0.0 --backend github --artifact dist/agent-dev-kit-6.0.0.tar.gz --dry-run
```

`release build` 默认要求 source distribution 对应 clean Git commit，并把 commit、tree、dirty 状态和 source distribution digest 写入制品。只有隔离测试快照可显式使用 `--allow-unbound-snapshot`；该制品会标记 `release_eligible=false`，不得进入 rehearsal、publish 或 Software M5 release evidence。

`release rehearse` 只接受 checksum 匹配且 candidate 版本更高的本地 artifact；它在临时 target 安装上一版、升级候选版、核验 receipt，再回滚并比较上一版受管资产 hash。rc.1 legacy bundle 或缺少当前必填 target contract 字段的上一版会在 release-only migration boundary 建立受管 receipt，再执行 rollback-before-install；active loader 仍 fail closed。candidate 回滚后，从保留的上一版 artifact 重装并逐文件比对 managed hashes，证明 fallback anchor 可用。build 在归档前校验 SPDX 2.3 SBOM 的 package/relationship 完整性并把 SBOM SHA256 写入 release manifest；GitHub release workflow 使用 SHA-pinned `actions/attest` 为 tarball 生成 provenance。该命令不创建 tag、不上传制品、不调用远端 backend。rehearsal、runtime smoke、timing 和 campaign state 属于 checkout 内的验证证据，不进入 source distribution，避免制品 SHA 与其自身验证报告形成循环依赖。

`release runtime-build` 按显式 Profile 构建 `adk-runtime-bundle/v1`，只包含版本化 Skill support tree、bundle manifest、逐文件 checksum、许可证和 SPDX SBOM。它是供外部 handoff target 导入的 platform-neutral Runtime Bundle，不是 Codex direct export；制品不包含 ADK Python 实现、测试、内部 change evidence 或 source distribution，也不会写任何运行目录。
