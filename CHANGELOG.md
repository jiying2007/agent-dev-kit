# Changelog

## Unreleased

## v7.0.14 (2026-09-22)

### Manifest format SSOT
- Bind format/CRLF/tab checks to canonical `manifest.json` instead of the retired `manifest.yaml` path.
- Add a regression ratchet that rejects any return of the retired YAML path in the format gate.


## v7.0.13 (2026-09-22)

### Canonical profile coherence authority
- Retire the `scripts/check-profile-coherence.sh` shell alias and invoke `agent_dev_kit.profile_coherence_contract` directly from tests and usage documentation.
- Preserve both human-readable and summary-JSON validation paths, and ratchet the retired shell entrypoint against reintroduction.


## v7.0.12 (2026-09-22)

### Test registry closure
- Remove three unowned retired shell tests that targeted superseded manifest/skill-governance semantics.
- Register current GitHub-governance and typed skill-relationship tests in the full regression suite.
- Add a machine gate requiring every `tests/test_*.sh` file to be owned by the regression runner or a dedicated GitHub workflow.


## v7.0.11 (2026-09-22)

### Canonical Workflow IR authority
- Retire the unused `scripts/check-workflow-ir.sh` Python-launch wrapper; Workflow IR regression imports the canonical `agent_dev_kit.workflow_ir` authority directly.
- Ratchet Workflow IR regression and active-doc governance against reintroducing the retired shell entrypoint.


## v7.0.10 (2026-09-22)

### Canonical release validation authority
- Retire the unused `scripts/release-validate.sh` compatibility bounce; release workflows and operators use the canonical `scripts/devkit.sh validate --strict` path directly.
- Ratchet validation regression and active-doc governance against reintroducing the retired alias.


## v7.0.9 (2026-09-22)

### Canonical harness command authority
- Retire the pure `scripts/check-harness-readiness.sh` bounce and keep `scripts/devkit.sh harness readiness` as the only public Harness readiness command path.
- Move capability-health evidence to the canonical CLI, keep Harness behavior tests on the canonical entrypoint, and ratchet the retired wrapper against reintroduction.


## v7.0.8 (2026-09-22)

### Evaluation CLI bounded context and coupling ratchet
- Split Evaluation command parsing and dispatch into `evaluation_cli.py`, removing campaign/evaluation/repository-evaluation domain fan-out from the public CLI through a real bounded-context boundary.
- Restore Catalog as a direct typed `catalog_contract` dependency instead of placing domain dispatch inside the environment/I/O-only `cli_runtime` substrate.
- Hard-cut stale `software_m5_eval_contract_rc4.json` CLI defaults; campaign and certify commands now default to the single canonical version-neutral `manifests/software_m5_eval_contract.json`.
- Make the reviewed Python import fan-out limit an ADK-owned architecture gate so downstream consumers no longer discover this coupling regression first.


## v7.0.7 (2026-09-21)

### CLI dependency boundary
- Keep `adk catalog` on the typed `catalog_contract` authority while routing it through the existing `cli_runtime` substrate, so the public CLI no longer grows a new domain import for every hard-cut command.
- Ratchet catalog regression against direct `cli.py -> catalog_contract` coupling; this restores the reviewed consumer maintainability fan-out budget without reintroducing a shell wrapper or compatibility path.


## v7.0.6 (2026-09-21)

### Canonical catalog command authority
- Route `adk catalog` directly to `agent_dev_kit.catalog_contract` while preserving canonical ADK-root resolution outside the repository cwd.
- Migrate catalog tests, taxonomy checks, goal evidence and capability health to the canonical CLI/Python authority; retire `scripts/catalog-assets.sh` and ratchet the removed compatibility surface against reintroduction.


## v7.0.5 (2026-09-21)

### Governance freshness and maintenance closure
- Re-review the three fast-moving external ecosystem references whose freshness windows expired, preserving method-only/runtime-disabled boundaries instead of extending dates blindly.
- Remove the last conditional test consumer of the retired `scripts/validate-assets.sh`; standalone ecosystem regression now uses the canonical `scripts/devkit.sh validate --strict` path.
- Replace the obsolete OpenTelemetry GenAI 1.42.0 schema-URL claim with an exact upstream-revision snapshot while upstream still publishes no GenAI Schema URL.
- Fold the current Ruff 0.16.8 and CodeQL 4.38.1 patch updates into one versioned maintenance release so Dependabot does not accumulate permanently unmergeable no-version PRs.
- Make `pyproject.toml` the single authority for exact dependency versions; product-maturity regression now validates the required dependency/tool set and exact-pin shape instead of duplicating every version literal.

## v7.0.4 (2026-09-19)

### Canonical command documentation
- Restore Software M5 commands to the single active `manifests/software_m5_eval_contract.json` contract and remove the nonexistent version-suffixed path.
- Make release examples derive the canonical source version at execution time instead of embedding a historical SemVer/artifact name.
- Ratchet active command documentation against version-suffixed M5 contracts and hard-coded release versions so future SemVer upgrades cannot silently stale the operator surface.


## v7.0.3 (2026-09-19)

### Release bootstrap and self-healing
- Keep source-version/bootstrap verification stdlib-only so exact-tag identity checks cannot depend on package dependencies that have not been installed yet.
- Move full synchronized version projection verification after CI dependency installation while preserving tag->commit and source-version guards before install/build work.
- Add exact-tag/manual repair inputs and automatic v7+ tagged-but-unreleased discovery; successful main promotion audits annotated tags, source versions, immutable Releases and exact asset sets, then reuses the canonical release workflow to repair missing Releases without moving tags.
- Preserve the failed v7.0.2 annotated tag at its exact source commit and allow the new self-heal path to publish its missing immutable Release from that source.


## v7.0.2 (2026-09-19)

### Complete version identity projections
- Move version verify/sync into typed `agent_dev_kit.versioning` and make the shell version manager a thin wrapper.
- Include the Software M5 campaign ID in synchronized source identity so the documented upgrade path cannot leave the repository in a guaranteed-failing state.
- Tighten canonical SemVer validation, align release checks with the same identity authority, and keep current documentation neutral to repository visibility.


## v7.0.1 (2026-09-19)

### Pre-merge release identity
- Require every pull request merged into protected `main` to advance source SemVer relative to its exact base before the required `contract-py3.11` check can pass.
- Centralize SemVer precedence in typed `agent_dev_kit.versioning`; release rehearsal and `version-manager compare` consume the same authority.
- Align documentation with the auto-promotion model: persistent main/release divergence is a release blocker rather than an expected steady state.


## v7.0.0 (2026-09-19)

### Release identity hardening
- Promote post-`v6.0.0` breaking cleanup under a new major SemVer identity instead of reusing the immutable 6.0.0 tag.
- Release promotion now fails closed when the source version tag already points to a different commit, creates annotated tags for new versions, and publishes a GitHub Release from the exact validated artifact bundle.
- Existing immutable tags, including `v6.0.0`, are never moved or rewritten.


### Active documentation and projection authority
- Active-document governance now discovers maintained root/docs/runbook/architecture/reference/spec/workflow Markdown automatically instead of relying on a small hand-maintained whitelist.
- Repo-relative `scripts/` and `tests/` references in active docs must resolve to real files; external-project commands use explicit repository/workspace boundaries instead of masquerading as ADK-local paths.
- Historical provenance has one explicit lifecycle exception; adding a historical marker to any other active document fails closed.
- Catalog, workflow matrix and routing matrix are deterministic manifest/frontmatter projections with byte-for-byte drift checks; volatile generation timestamps are removed.
- Current runtime documentation derives active target claims from `manifest.json`; retired Hermes runtime claims and retired validation/matcher/Runtime Control entrypoints are removed from current operational guidance.

### Stable governance-test naming hard-cut
- Renamed the active product-maturity gate to `test_product_maturity.sh` and removed the stale v5 identity from its pass contract.
- Renamed Skill Governance coverage to `test_skill_governance*`, restored it to both quick and full regression suites, and ratcheted the retired v3 entrypoints.
- Removed the no-op `quality-gate-check.sh --strict` compatibility flag; retired use now fails closed instead of being silently accepted.
- Runtime compatibility runbook now derives its target claims from the canonical manifest, removes the retired Hermes target claim and dead verification commands, and is covered by active-doc regression.
- Platform workflow file/display identity is stabilized as `platform`; the job context `platform-vnext` remains intentionally frozen because the active `main` ruleset requires that exact status context.

### ExecutionPolicy Python naming hard-cut
- Renamed the public execution-policy exception from `RuntimeControlError` to `ExecutionPolicyError`; no Python alias is retained.
- Renamed execution-policy regression entrypoints to `test_execution_policy*` while preserving all frozen `runtime_control.*` wire/schema identities.
- Added negative regression coverage so the retired Python symbol and test entrypoints cannot return.

### Validation CLI hard-cut
- Removed the legacy `scripts/validate-assets.sh` shim; `adk validate` now owns typed validation and strict governance orchestration directly.
- Strict summary JSON and process exit status now derive from the same aggregated failure set, preventing a pass JSON from preceding a later governance-gate failure.
- Validation tests, usage guidance and token-budget governance now target the unified CLI and reject reintroduction of the retired shim.

### Canonical matcher authority
- `agent_dev_kit.matcher` now owns Skill Content v2 eligibility, selection-group promotion, effect ceilings and escalation semantics; the old deterministic implementation is internal-only as `_matcher_kernel`.
- Deterministic evaluation, runtime evaluation, CLI routing, phase context and Skill relationships all consume the same matcher authority.
- Retired `matcher_vnext.py`, active `content-architecture-vnext` checker/fixture paths and the `skill_runtime_role` result alias are removed.
- Matcher results expose canonical `runtime_role` and typed `escalation_effects` arrays; Software M5 route-031 now expects its same-group primary `adk-requirements-triage`.

### Match CLI hard-cut
- Removed the standalone `scripts/skill-match.sh` wrapper; all matcher calls now route through the unified `adk match` command.
- Matcher root discovery and argparse identity no longer depend on the retired shell path.
- Match regression and token-context governance tests now exercise the same public CLI surface used by operators.

### Agent Platform stable surface
- Public Platform operations move to the unified `adk platform` command and stable `agent_dev_kit.agent_platform` implementation.
- Retired `platform_vnext.py`, `platform_vnext_cli.py`, `platform-vnext.sh` and `test_platform_vnext.sh` are physically removed.
- Contract registry producers bind to the stable module identity. The workflow file/display identity is `platform`; only the job/check context `platform-vnext` remains frozen because the active `main` ruleset requires that exact status context.

### Shell zero-compat follow-up
- Remove the deprecated `quality-gates.sh` delegate, removed fallback-sunset executable tombstone, and repository-only `bin/agent-dev-kit` alias.
- Removed the retired asset-taxonomy shell shim; taxonomy validation now calls the canonical typed Python contract directly. Remaining shell governance launchers describe their JSON manifest query path as current ownership rather than compatibility shims.
- Active-doc regression centrally rejects retired compatibility paths from returning.

### Export zero-compat follow-up
- `scripts/convert-assets.sh` is removed. `adk export` via the unified CLI is the sole maintained export surface.
- The retired wrapper can no longer advertise or route the removed `hermes-agent` target.

### Installer zero-compat follow-up
- Transactional install/rollback accepts only `adk-install-receipt/v3`; receipt v1/v2 compatibility parsing and rollback branches are removed.
- `scripts/install-assets.sh` is removed. `adk install plan/apply/rollback` via the unified CLI is the sole maintained install surface.

### Zero-compat hard-cut follow-up
- Release rehearsal now accepts only the current strict source contract and release-manifest v2; the executable pre-contract bundle migration path and release-manifest v1 acceptance are removed.
- Software M5 evaluation uses one canonical `manifests/software_m5_eval_contract.json` bound to the current ADK source version; active rc2-rc7/v5 snapshot copies are removed.
- Release source-distribution inventory is fail-closed: every declared source path must exist, and stale `contexts/` / `NAVIGATION.md` inventory entries are removed.

## v6.0.0 (2026-09-18)

### Breaking compatibility cleanup
- `adk` is the single installed CLI. `match`, `phase-context` and `skill-relationships` all resolve through one Python command surface; compatibility console scripts and legacy command aliases are removed.
- Skill relationships are fully typed in `skill_relationship_contracts_v2.json`; `manifest.json` no longer carries `depends_on`.
- Phase context is fully semantic in `phase_context_contract_v2.json`; manifest phase-to-Skill path mirrors are removed.
- `agent_dev_kit.execution_policy` is the only Python execution-policy namespace; the 5.x `agent_dev_kit.runtime_control` facade is removed. Existing versioned wire-schema identities remain unchanged.
- Abandoned manifest physical-split readiness scaffolding is removed. The active manifest contract remains one canonical `manifest.json` with read-only in-memory composition checks.

### Governance
- Contract registry binds routing to `matcher_vnext`, phase/relationship contracts to v2 hard cuts, and execution decisions to `execution_policy`.
- Regression tests now reject reintroduction of legacy dependency metadata, phase path mirrors, retired Python aliases, and multiple installed ADK command surfaces.

## v5.1.0 (2026-09-12)

### Agent Platform vNext
- 收敛 Agent Platform vNext 的平台中立 primitives、Runtime Adapter/Control、Workflow IR、Trace/Eval 与 runtime bundle identity 证据链。
- 强化 direct target、external handoff 与 runtime certification 边界；不把 experimental target 误报为 native/certified。
- MCP 官方资料 freshness 统一由 canonical source 治理，避免平行时间戳和过期状态漂移。

### 治理与供应链
- 增加 Dependabot、CodeQL、dependency review，并保持 Actions SHA pin、最小权限、OIDC/Cosign promotion evidence 与 release provenance attestation。
- Branch GC 升级为 fail-closed exact-head 治理：merged PR head 与显式 reviewed ancestor 都必须在 DELETE 前重新验证；历史 CLI support 分支已由 exact-SHA ancestry proof 退役。
- 版本管理器迁移到 canonical `manifest.json`，并强制 `manifest.json`、`pyproject.toml`、`__version__`、`.version-lock` 与 README 发布身份同步。

### 成熟度语义
- 产品成熟度、ADK 组件发布成熟度和 runtime conformance 分离管理；不再用产品 M3/M5 术语表达组件版本状态。

### 发布边界
- `5.1.0` source candidate 只有在 exact-main fresh CI、signed promotion evidence、`v5.1.0` exact tag、tag-triggered release workflow 与 GitHub Release 均形成证据后才视为远端发布完成。


## v5.0.0-rc.2 (2026-08-30)

### 发布候选加固
- 发布制品默认绑定 clean Git commit、tree 与 source distribution digest；dirty 或非 Git 快照只能显式构建为不可发布制品。
- 本地 CI parity 使用稳定 source snapshot、双 Python 全量回归 receipt 和摘要输出，避免重复验证与无效日志消耗。
- 精确区分 legacy bundle 迁移和不兼容 target contract hard cut，保留 fail-closed 边界。

### 候选边界
- `rc.2` 替代 `rc.1` 作为当前候选身份；不改写 `rc.1` 历史，也不代表 tag、远端 Release、source-to-live 或 Software M5 field certification 已完成。

## v5.0.0-rc.1 (2026-08-30)

### 破坏性变化
- core Profile 收敛为平台中立资产；嵌入式能力仅由显式 Profile 承载。
- target contract 升级到 v2；routing、Workflow IR、Runtime Control 和运行证据合同切换到新版本，不提供隐式旧格式回退。

### 新增
- 增加 Workflow IR v2、Trace Summary v2、Evidence Graph、Run Evidence Composition 与 Effect Comparator。
- 增加 receipt 驱动的 Agent Value 生命周期，显式记录覆盖率、信任级别和评估窗口。
- 增加 native target conformance receipt、privacy reference 和显式 per-run trace emitter。

### 候选边界
- 本版本是本地 release candidate，不代表已完成双运行时 campaign、30 天 field pilot、tag、发布或 source-to-live。
- manifest 数据格式继续使用 `schema_version: 4.0.0`；产品发布版本和 manifest schema 版本独立演进。

## v4.0.0 (2026-08-24)

### Breaking
- Goal、Token、progress、checkpoint、retry、evidence 与 delivery gate 统一由唯一 Runtime Control Engine 决策。
- 删除独立 token monitor / execution guard 实现、CLI、schema 和兼容路径。
- Codex runtime 通过 pinned ADK package 使用 Engine；不保留 fallback、alias、dual-read 或 dual-write。

## v3.1.0-rc.7 (2026-08-02)

### 新增
- 增加 task-cost profile 与 CLI receipt，用有界字段表达任务复杂度、上下文预算、验证强度和归档候选要求。
- Knowledge Hub 上下文查询增加显式项目路由、分层 receipt、review SLA packet 与有界 capture summary。

### 改进
- Token 预算门禁区分 soft/hard limit，并为 AGENTS、Skill、Workflow 与 manifest 提供可解释余量。
- 根工作区门禁区分 `working-tree` 与 `release-clean`，开发态绑定同轮 fingerprint，发布态继续要求 ADK clean state。
- Codex 资产交付增加 plan v3 precondition、按需 workflow activation、成本投影和 already-applied no-op 收敛。

### 发布边界
- RC7 使用 checksum-bound RC6 artifact 执行本地升级、候选回滚和 RC6 hash 恢复演练。
- 本轮授权 source commit 与 push；不创建 tag、远端 Release，不提升 Knowledge Hub active 状态。

## v3.1.0-rc.6 (2026-07-31)

### 新增
- MCP `2026-07-28` protocol governance contract 经固定 Go SDK 的 schema、client/server、auth 和 rollback 证据后激活；runtime 与 Tasks、Apps、extensions 继续关闭。
- 嵌入式远程调试增加分层连通性、设备失联熔断、artifact/mutation gate 和 HIL 分阶段扩大合同。
- 目标架构报告支持由机器 SSOT 管理连续 G11+ 项目级优化条目。

### 发布边界
- RC6 通过 RC5 到 RC6 本地 artifact 升级/回滚演练建立新 release baseline。
- Codex source-to-live 未自动执行，保持独立 owner 授权门禁。

## v3.1.0-rc.5 (2026-07-19)

### 新增
- 增加平台中立 `skill_invocation` SSOT 和 direct-target mapping；Claude Code 支持 `explicit-only`，未核验等价字段的 target fail closed，Codex 继续由 external handoff adapter 承接。
- 增加 task-package v2 typed validator，区分 decision/research/prototype/implementation，并用 permission/exit gate 阻止探索票直接进入实现。
- 增加 architecture hotspot/YAGNI scope 与 prototype evidence provenance/retention 合同。

### 破坏性变化
- 删除 task-package v1 活跃合同与 reader，不补默认字段、不双写；所有机器消费任务包必须迁移到 v2。
- Codex Skill metadata 硬切官方嵌套 `interface` 结构；顶层 legacy metadata 与显式 `allow_implicit_invocation: true` 不再接受。

### 门禁
- 新增 invocation target mapping、未知 override、work-item 越权、prototype 缺 provenance、架构无理由扩域的正负回归。
- external source 只吸收方法，不安装、复制或运行 `mattpocock/skills`、Claude plugin、hook/MCP 或 in-progress Skill。

## v3.1.0-rc.4 (2026-07-19)

### 新增
- 增加 `external-practice-curator`、显式 opt-in 的 `adk-external-practice-absorption` 和 `external-practice-absorption` Workflow，统一承接 GitHub、GitLab、Gitee、OpenAI/Codex 官方、Anthropic/Claude 官方、微信公众号与人工证据的候选审查和独立决策 handoff。
- 增加 `research-intake` profile 的 Agent 默认 Skill 闭包，并保留 optional Skill 必须显式选择的安装边界。

### 破坏性变化
- 删除 `adk-intake-workflow`，不提供别名、warning wrapper 或双写兼容；调用方必须迁移到新的 candidate/decision/change 工作流。
- 外部实践 collector/curator 固定为 `read-only`、`report-only`，不得自批、自动复制、安装、提交、发布或写 live runtime。

### 修复
- file-mode 与 security inventory 在 live Git 工作树中跳过已删除路径的内容扫描，删除本身继续由 status、inventory 和 review 门禁负责；显式只读 inventory 仍对缺失文件 fail closed。
- Workflow 合同与 taxonomy 测试同步一等 Workflow 数量、optional closure 和 lifecycle 顺序。

## v3.1.0-rc.3 (2026-07-18)

### 修复
- 根工作区性能包装器现在执行 quick timing 的严格预算门禁；ADK quick suite 执行 quick manifest validation，把产品成熟度与 catalog/taxonomy 重型回归保留在 full（根性能包装器仍单独执行产品成熟度），避免重复工作并为 120 秒预算保留抖动余量。
- install manifest、Draft 2020-12 schema、copy-only installer 和用户文档统一；关键 routing、dependency、reference、context、change-set 与空 MCP 合同改为 typed fail-closed schema。
- Harness readiness 要求结构化权限边界，拒绝否定语境伪证据，并对未来或超过 freshness 窗口的验证日期输出 blocker。
- Python 打包元数据迁移到 PEP 639 SPDX license 表达式，并增加 Python 3.11/3.12 Docker 本地 CI parity runner：源码快照只读、固定非 root 身份、gates 无网络、dependency audit 独立联网，并核验 base/definition/image identity；本地结果不能替代 release provenance 或远端 CI 状态。

### 破坏性变化
- 发布支持基线提升到 Python 3.11+，运行依赖固定为 `PyYAML==6.0.3` 与 `jsonschema==4.26.0`；CI 最低版本同步到 3.11。
- 关键 nested manifest object 现在执行 typed schema 并拒绝未知字段；自定义 manifest 升级前需运行 `bash scripts/devkit.sh validate --strict`，修正错误类型，并把确需保留的产品级扩展迁移到顶层 `x-<name>` namespace。

## v3.1.0-rc.2 (2026-07-13)

### 修复
- direct target 输出改由 versioned `TargetContract` 与单一 `TargetAdapter` 生成；Claude Code/OpenCode 使用原生 `agents/<name>.md` 与 `skills/<name>/SKILL.md`，Hermes 明确为 Skill-only。
- Agent/Skill frontmatter 补齐目标必需字段、显式 Agent permission profile 和 `metadata.adk` provenance；Skill support directories 随主文件确定性导出。
- export/install 共用 renderer；export manifest 升级到 v2，install plan 升级到 v2，receipt 升级到 v3，并保留 v1/v2 receipt rollback 读取。
- install plan 绑定 active receipt SHA256、UUID、时区时间与 24 小时 TTL 上限；legacy fallback 演练会从保留的 rc.1 artifact 重装并比对 managed hashes。

### 门禁
- direct target 保持 `experimental`，只有真实 runtime discovery/load/trigger/permission smoke 完成后才允许提升 stable。
- manifest schema 升级到 3.1.0，并由 `jsonschema==4.23.0` 按 Draft 2020-12 实际执行。
- CI 增加 ShellCheck、Ruff、pip-audit 和 OpenSSF Scorecard；release build 校验 SPDX SBOM，并由 SHA-pinned `actions/attest` 生成 provenance。
- 性能基准增加 CLI cold-start、10x plan/I/O 与 peak allocation；effect eval 增加 24 个 OOD/adversarial route+safety+trace+outcome case，并要求 routing ablation 至少产生 0.1 的准确率差值。
- `3.1.0-rc.2` 修复 target conformance，不代表 M4/M5 或 terminal maturity 认证。

### 增强
- 新增 `adk-runtime-router` 核心技能，作为 adk-first 运行时路由入口，统一 primary/supporting/fallback 裁决。
- 新增 `adk-test-strategy`、`adk-code-review-loop`、`adk-parallel-agent-governance`、`adk-worktree-governance`、`adk-branch-closeout` 五个核心技能，减少对 Superpowers TDD/review/parallel/worktree/branch closeout fallback 的默认依赖。
- 扩充 `adk-requirements-triage` 与 `adk-systematic-debugging` 自然语言触发覆盖，降低真实任务漏匹配概率。
- 新增 `docs/reference/fallback-sunset-matrix.md` 与 `fallback-sunset-matrix.tsv`，跟踪 fallback 到 adk 原生能力的下线状态。
- 新增 `scripts/check-fallback-sunset.sh`、pilot 证据库和嵌入式优先模板，防止在缺少真实能力面证据时提前宣布 sunset。
- 调整 `adk-test-strategy` 为嵌入式优先、兼容通用工具链脚本的测试策略定位。
- 强化 fallback 下线门禁：逐行执行 `devkit.sh match --text`、校验命中 skill 属于等价能力、检查 active-fallback 复核日期，并输出 routing/profile/pilot/handoff/live replacement score。
- fallback 下线门禁新增 `--score-tsv` 与 `--summary-json`，并检查 pilot index 与 evidence 文件状态、章节是否一致。
- fallback 下线门禁新增 `live_requirement`、按状态评分阈值和 `scripts/pilot-readiness.sh` 独立 pilot 成熟度检查。
- 将 adk 定位修正为嵌入式全栈，覆盖 SoC、MCU、Linux、RTOS、驱动、组件、设备应用、上位机、产测诊断工具和交付验证，不扩展到通用 Web/互联网后端/云原生。
- 扩展嵌入式全栈范围为完整工程闭环：芯片/板级约束、启动链、BSP/rootfs、OS/runtime、验证、发布、量产和现场维护；新增 `adk-production-field-readiness` 承接量产/现场 readiness。
- 为 active-fallback 能力补充 discovery、子代理审查、skill 生命周期、长任务恢复和嵌入式全栈测试矩阵模板。

### 修复
- 生命周期文档移除未落地的 `adk-*workflow` 与 `adk lifecycle` 占位入口，改为当前 `scripts/devkit.sh` 真实命令。
- 维护文档统一使用 `adk-*` 技能名称，减少 Superpowers 迁移期命名漂移。

## v3.1.0-rc.1 (2026-07-13)

### 新增
- 新增 `doctor`、`lock`、`eval campaign/certify` 和 `release rehearse` 公共入口。
- 新增 60 任务、Codex/Claude、baseline/ADK、3 trials 的软件 M5 评测契约，固定模型、预算、重复试验和统计门槛。
- 新增 export/install/rollback/campaign 的 portable single-writer lock，支持显式状态检查和基于 lock ID 的人工清理。
- 新增 checksum 约束的本地 release 升级/回滚演练，校验 top/source manifest、receipt 和受管资产 hash。

### 改进
- 将确定性 matcher 收敛为一次结构化加载的 Python core，保留 `skill-match.sh` 参数、输出和退出码兼容。
- campaign 结果逐任务原子落盘，支持 resume，并绑定 manifest、contract、tasks、frozen plan、runtime 版本、模型和 record hash。
- Claude 主调用与一次重试的最坏费用受 `$150` 总上限约束；重试的 latency、token 和 cost 全部进入非回退门禁。
- 安装 receipt 升级为 `v2`，校验 receipt、替换备份和前序 receipt 的 SHA256，同时保留 `v1` 升级回滚兼容。
- runtime 调用增加有界超时和异常归一化；writer lock 禁止清理仍存活 owner，export 双重故障保留人工恢复目录。

### 成熟度边界
- `3.1.0-rc.1` 是 M5-ready release candidate，不代表已认证 M5 或 terminal maturity。
- 最终 `3.1.0` 仍要求 30 天试点、至少一个独立真实软件仓、第二位 operator、双 runtime campaign 和完整 field evidence。

## v2.9.0 (2026-05-17)

### 破坏性变更
- 移除重复调试技能 `adk-diagnose-loop`，统一由 `adk-systematic-debugging` 承接诊断闭环。
- 移除重复产物门禁 optional skill `adk-artifact-gated-lite`，统一由核心 `adk-artifact-gating` 承接高风险门禁。
- Codex 交付硬切换为 `agent-dev-kit -> ~/codex -> ~/.codex`，禁止直接安装到 `~/.codex`。

### 增强
- manifest 新增一等 `workflows` 与显式空 `mcp_servers` 声明。
- Codex handoff 新增 `workflows.json` 与 `mcp_servers.json` manifest fragment。
- 严格校验新增 context layer 路径、workflow 声明和 SKILL.md 入口长度门禁。
- 长 SKILL.md 拆分到 `references/details.md`，减少默认上下文加载。

## v2.8.0 (2026-05-12)

### 修复
- manifest.yaml: 修复 33 个 skill 的重复 quality_tier YAML 键
- manifest.yaml: 补充 7 个缺失 Profile 定义 (personal-core, embedded-fullstack, team-core, openspec-driven, large-refactor, incident-response, research-intake)
- 文档引用: 修复 7 个文件中的版本锁定引用 (统一为 2.8.0)
- 导航链接: 修复 NAVIGATION.md 3 个断裂 Runbook 链接
- Runbook 索引: 修复 runbooks/README.md 3 个错误文件名
- 脚本引用: 修复 check-global-codex-health.sh 和 check-adk-harden-readiness.sh 路径引用
- 统计数据: 更新 README.md 和 AGENTS.md 中的过时统计数字

### 统计
- Agents: 10 个
- Core Skills: 33 个
- Optional Skills: 9 个
- Profiles: 10 个 (新增 8 个)
- Scripts: 26 个

## v2.7.0 (2026-05-10)

### 增强
- VibeFlow 生命周期框架吸收 (8 阶段: Spark→Design→Tasks→Build→Review→Test→Ship→Reflect)
- Gate 机制设计原则 (4 问评估标准)
- 知识分层架构 (L0-L4) 文档化
- 仓库深度分析报告更新

### 新增
- docs/workflows/lifecycle.md: 生命周期工作流文档
- docs/workflows/gate-design.md: Gate 设计原则文档


## v2.6.0 (2026-05-06)
### 新增
- 脚本 smoke 测试：test_scripts_smoke.sh 覆盖 11 个脚本

## v2.5.0 (2026-05-06)
### 修复
- Trigger 冲突：修复 6 个 skill 的 trigger 重复
- Skills last_updated 日期更新为 2026-05-06

## v2.4.0 (2026-05-06)
### 修复
- manifest.yaml optional_skills 列表错误修正
- Docs 中 7 个脚本引用路径修正
- adk-data-fetch SKILL.md 创建

## v2.3.0 (2026-05-06)
### 增强
- 10 个 Agents 全部充实（50-67L → 103-123L）
- 7 个 Optional Skills 全部充实（59-77L → 128-152L）

## v2.2.0 (2026-05-06)
### 增强
- 28 个 Core Skills 全部充实（65-106L → 80-195L）
- Skill 内容质量测试：test_skill_content.sh（196 检查点）

## v2.1.0 (2026-05-06)
### 增强
- Routing 全覆盖：28/28 skills
- user-story-template 扩充（29L → 235L）

## v2.0.0 (2026-05-05)

### 新增
- Anti-Rationalization 机制：每个 p0 skill 添加"合理化借口拦截"表
- Skill 路由表：manifest.yaml 新增 routing 字段，支持中英文意图映射
- 阻塞模板：templates/blocked.md 和 ready.md
- 执行计划模板：templates/exec-plan.md（六要素）
- 质量评分卡：templates/quality-score.md（五维度）
- Agent 交接协议：templates/agent-handoff.md
- 健壮性规范：SKILL.md 新增 robustness 章节要求
- 渐进式披露：skill references/ 子目录支持
- Profile 冲突检测：manifest.yaml conflicts_with 字段
- Skill 依赖图：manifest.yaml depends_on/enables 字段
- 新增 Skill: adk-structured-requirements-questioning, adk-code-simplification, adk-context-engineering
- 新增 Skill: adk-chinese-commit-conventions, adk-chinese-code-review
- 新增 Optional Skill: adk-fetch-url-content, adk-email-imap-fetch
- 文档导航: docs/NAVIGATION.md
- 测试: test_anti_rationalization.sh, test_routing.sh, test_skill_dependencies.sh, test_profile_conflicts.sh

### 统计
- Agents: 10 个（不变）
- Core Skills: 28 个（+6）
- Optional Skills: 9 个（+2）
- Profiles: 10 个（不变，新增 trigger_examples）
- Templates: 5 个（新增）
- Routing: 21 条意图映射（新增）
- Tests: 25 个测试文件（+4）

### 修复
- 版本撕裂：manifest(1.0.0) vs README(0.3.0) 统一为 2.0.0
- 配置冲突：manifest default_mode 从 symlink 改为 copy

### 改进
- 42 个文档新增统一导航索引
- Profile 支持中文触发词路由（intent_zh + trigger_examples）
- 生产运维脚本验证和测试覆盖

## v1.0.0 (2026-05-02)

- 初始生产级发布
- 10 Agent + 22 Skill + 7 Optional Skill + 10 Profile
- Evidence Index 机制
- propose→apply→verify→review→archive 工作流状态机
- 24 脚本 + 21 测试文件 + 42 文档 + 26 Runbook

---

# 变更日志 - 1.0.0

## 版本信息
- 版本号: 1.0.0
- 发布日期: 2026-05-05
- 维护者: aiot03

## 变更内容

### 新增功能
- 完善使用指南和示例文档
- 增加最佳实践和故障排除指南
- 增加贡献指南
- 完善安装备份、回滚机制
- 增加健康检查和监控能力
- 增加版本锁定和升级路径

### 改进优化
- 增强测试覆盖
- 完善质量门禁
- 优化文档体系

### 已知问题
- 无

## 升级指南
1. 备份当前版本
2. 下载新版本
3. 运行健康检查
4. 验证功能

## 相关链接
- 文档: docs/
- 快速入门: docs/quick-start.md
- 故障排除: docs/troubleshooting.md
