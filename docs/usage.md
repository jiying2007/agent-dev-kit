# Usage

`agent-dev-kit` 是通用 ADK 资产包。它维护 Agent、Skill、Profile、Workflow 和治理契约，并通过显式 direct `tool_targets` 导出到不同运行时；需要外部声明式链路承接的运行体系进入 `external_handoff_targets`，core 不绑定任何单一平台。

本文先说明如何用现有 Skills 完成任务，再提供源码管理命令速查；安装、升级和目标环境细节见 `docs/adk-usage-guide.md`。

## 按任务使用 Skills

已安装资产时，先给任务目标和现有材料，Agent 按当前阶段选择入口。一个请求通常只需要一个 primary；辅助能力只在当前步骤确实需要时加载。

| 当前要解决的问题 | 最少有用输入 | 应得到的可用结果 |
| --- | --- | --- |
| 澄清需求、头脑风暴、挑战方案 | 目标、约束、已有决定；未知项可以明确未知 | 少量真正改变选择的问题、可行方案、推荐与验收；明确实施请求不重新访谈 |
| 计划、实现与持续推进 | 现有合同或任务、当前状态、相关源码与测试入口 | 可关闭的工作切片、真实改动及结果；继续已有目标，恢复阻塞与在途工作 |
| 驱动、BSP、RTOS、协议、接口 | 目标芯片/板/运行模型、规格、工具链、消费者 | 适配目标的设计或实现、构建/测试及未上板边界；源码任务与设备操作分别判断 |
| 调试、core、性能、资源优化 | 故障或目标指标、输入负载、匹配制品、现有观测 | 最短可证伪实验、根因/热点证据；定位任务可止于诊断，比较任务再验证收益 |
| 测试、Review、静态分析、安全 | 要证明的行为或待核实的意见、变更、测试/扫描入口 | 用例或已授权测试代码、真实 finding 与复现；误报、未覆盖范围分别说明 |
| 文档、ADR、复盘、交接 | 读者、用途、素材与既有格式 | 能直接使用的正文或指定局部修改；事实、数字、未决状态保真 |
| 发布、迁移、归档、分支收尾 | 版本、目标、验收结果、现有权限与恢复方案 | 可执行的发布/迁移准备或收尾结果；外部实际完成以真实回执为准 |
| 检索、资料获取、记忆和上下文 | 已授权来源、具体问题或筛选条件、当前需要的事实 | 有来源的可用内容、必要原文入口、明确缺失；不把完整历史反复加载 |

不必先填写一整套表：能从仓库、已有状态或材料读出的信息先读取；只在缺失信息会改变当前决定时询问。已有授权可覆盖的步骤连续推进，支持完整交付；超出权限的设备、发布等操作仍走原审批。简单任务使用已有轻量路径和定向验证，高风险按实际边界升级。

**结果要求随请求变化。** “只分析”交付分析；“写测试/修复/修改文档”在已有实施授权内交付实际文件和验证；“继续”从当前状态接续。不能把计划写完、命令启动或模板填满作为实际工作完成。

**缺工具时先给出仍能完成的结果。** 例如无目标板时完成源码/交叉构建并标出待上板项；没有 ABI 类型信息时只报告已核实的符号差异；获取到网页空壳时报告正文未取得。不要把未执行算成功，也不要为了完成普通任务安装 ADK 的内部构建环境。

完整清单由 [Manifest 生成的目录](agent-skill-catalog.md) 提供，包含全部 core 和 optional Skills；[路由矩阵](reference/skill-routing-matrix.md) 说明主入口与辅助关系。以下命令用于 ADK 源码工作区内查询，不是用户每次使用 Skill 的前置步骤：

```bash
bash scripts/devkit.sh catalog find --type skill --keyword 调试
bash scripts/devkit.sh catalog find --type optional-skill --keyword "fetch data"
bash scripts/devkit.sh match --skill adk-planning-execution-loop --text "按现有计划继续执行"
```

ADK 构建与管理环境为 Python 3.12.x，固定依赖为 `PyYAML==6.0.3` 与 `jsonschema==4.26.0`；已导出纯 Skill 资产不依赖 ADK Python。发布前安装 `.[quality]` 并执行 Ruff 与 pip-audit；工具缺失或审计源不可用时不得声称质量门禁通过。

升级现有自定义 manifest 时，先执行 `bash scripts/devkit.sh validate --strict`。关键 nested object 已改为 typed schema，旧的未知扩展字段、字符串冒充数组/布尔值以及缺失必填项会 fail closed；应按 `manifests/manifest.schema.json` 迁移。确需保留的产品级扩展元数据应移动到顶层 `x-<name>` namespace，不能通过放宽核心 schema 保留未声明行为。

## 1. 预检查

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh validate --quick
bash scripts/check-runtime-boundary.sh
PYTHONPATH=src python3 -m agent_dev_kit.asset_taxonomy_contract --root . --summary-json
bash scripts/check-official-docs-governance.sh --summary-json
bash scripts/devkit.sh test
```

说明：

- `validate --strict`：检查 manifest、路径、frontmatter、profile 引用、Agent 章节契约、Workflow 一等资产契约、context layer、skill 入口长度和质量分级。
- `validate --quick`：快速结构检查，适合编辑中间态。
- `runtime-boundary`：检查 ADK core 是否保持平台中立，防止平台专属 handoff、运行目录写入残留和 direct/external target 边界混用。
- `asset-taxonomy`：检查 skill/workflow 分类、manifest 物理顺序、profile 生命周期顺序和场景路由矩阵。
- `official-docs-governance`：检查官方资料 freshness、提升状态和平台中立契约。
- `test`：全量回归，包含 validate、格式、内容质量、文件权限、事务安装、profile coherence、optional、export、workflow contract、catalog、trigger matrix、governance 和 smoke。
- `catalog build`：生成 Agent/Skill/Workflow/Profile 索引，并在默认输出模式下同步生成 `docs/workflow-contract-matrix.md` 和 `docs/reference/skill-routing-matrix.md`。
- `harness readiness`：只读汇总目标仓 Harness 证据；默认 report-only，不用加权分数替代关键维度判断。
- 资产命名与边界标准见 `docs/asset-contract-standard.md`；历史角色型资产硬切换，不保留兼容 alias。

CI / runner 复现：

```bash
PATH=/usr/bin:/bin bash scripts/devkit.sh validate --strict
PATH=/usr/bin:/bin bash scripts/check-format.sh
PATH=/usr/bin:/bin bash tests/run_all.sh
```

ADK active scripts 不直接依赖 `rtk`；本机 Codex 会话只在操作者命令边界加 `rtk`。

## 2. Profile 选择

| Profile | 推荐场景 |
|---|---|
| `core` | 通用 ADK 主干能力 |
| `personal-core` | 个人通用 ADK 核心配置 |
| `embedded-fullstack` | 嵌入式全栈开发配置 |
| `release-hardening` | 发布前强化 |
| `team-core` | 团队交付与交接 |
| `large-refactor` | 大型重构 |
| `incident-response` | 事故响应 |
| `research-intake` | 参考资料吸收 |

Profile 继承一致性检查：

```bash
PYTHONPATH=src python3 -m agent_dev_kit.profile_coherence_contract --root .
```

## 3. 安装和导出

安装通过 plan/apply/receipt/rollback 事务把 Agent/Skill 复制到显式 target。plan 会阻断未托管冲突和过期/漂移输入；`symlink` 模式未实现并会 fail closed：

```bash
bash scripts/devkit.sh install plan --tool claude-code --target /tmp/adk-claude-target --mode copy --profile core --extra-profile release-hardening --output /tmp/adk-plan.json
bash scripts/devkit.sh install apply --plan /tmp/adk-plan.json
bash scripts/devkit.sh install rollback --receipt /tmp/adk-claude-target/.adk-install-receipt.json
```

跨版本升级时，在候选源码下执行 plan/apply，并为两步显式传入 `--previous-source /reviewed/previous-adk-source`；该目录必须是产生当前 receipt 的已审查精确源码。回滚升级也在候选源码下执行，并用相同参数验证将恢复的旧 receipt 与备份。首次安装或同版本重装可省略此参数。保留候选与旧版源码，直到不再需要对应回滚。

旧源码仍需满足当前 manifest/target 合同，并可由当前受信 renderer 重现；该参数不会动态执行旧源码中的 Python，也不提供任意历史版本迁移。恢复 A 后若需继续回滚 A，可用已安装的新版 `adk` 命令并设置 `ADK_ROOT=/reviewed/adk-a` 选择 A 资产来源；必要时再提供 A 的前序来源。

历史库存恢复保留 manifest/contract、逐文件内容和 mode 校验；target 文档自然到期不会使已安装资产失去恢复依据。新安装、导出和 target 检查仍要求当前文档未到期，恢复不续期文档或改变 runtime/native 资格。

export 用于生成 target 格式的确定性交付目录：

```bash
bash scripts/devkit.sh export --target claude-code --profile embedded-fullstack --out dist --clean
bash scripts/devkit.sh export --target opencode --profile team-core --with-optional-skill adk-security-supply-chain --out dist --clean
```

参数说明：

- `--tool`：`claude-code|opencode`。
- `--target`：导出目标，取值来自 `manifest.json:tool_targets`。
- `--mode`：仅支持 `copy`；`symlink` 返回 `unsupported_install_mode` 且不生成 plan。
- `--profile`：主 profile，默认 `core`。
- `--extra-profile`：可选叠加 profile，可重复。
- `--with-optional-skill`：按需叠加 optional skill，可重复。
- `--out`：导出输出根目录；根目录、target 目录及祖先均不得是符号链接，路径不得包含 `..`。
- `--clean`：在 writer lock 内检查路径身份后替换当前 target 的导出目录，不通过链接清理其他目录。
- `--output`：安装 plan 输出路径。
- `--ttl-minutes`：安装 plan 有效期。

生产纪律：

- tool target 必须显式声明，不能把平台专属路径写进 core。
- Codex 当前不是 direct tool target；Codex 交付由外部 `~/codex -> ~/.codex` source-to-live 链路承接，并记录在 `manifest.json:external_handoff_targets.codex`。
- OpenAI/Codex 官方资料只作为 `manifest.json:reference_sources` 和 governance manifest 的引用来源，不表示 runtime enablement。
- install/export 的输出是交付物，不是绕过目标运行时治理的理由。
- 写入真实用户运行目录前必须有 dry-run、备份或回滚路径。

## 4. 目录索引与触发匹配

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh catalog find --type optional-skill --keyword 事故
bash scripts/devkit.sh match --skill adk-requirements-triage --text "收到模糊需求或跨团队需求时"
bash scripts/devkit.sh match --skill adk-planning-execution-loop --text "按现有计划继续执行"
```

技能组合规则：

- 一个场景只有一个 primary skill。
- supporting skills 只补检查项，不抢入口。
- 多技能冲突时使用 `adk-skill-composition-governance`。
- 第三方资产进入运行环境前使用 `adk-security-supply-chain`。

## 5. 工作流命令

```bash
bash scripts/devkit.sh propose --change can-fd-bringup --title "新增 CAN-FD bring-up"
bash scripts/devkit.sh apply --change can-fd-bringup
bash scripts/devkit.sh verify --change can-fd-bringup
bash scripts/devkit.sh review --change can-fd-bringup --result pass --blockers 0 --majors 0 --minors 1
bash scripts/devkit.sh archive --change can-fd-bringup
```

命令级 Evidence Index：

```bash
bash scripts/evidence-index.sh append --file docs/changes/can-fd-bringup/negative-results.md --command "bash tests/run_all.sh" --exit-code 0 --summary "all tests passed" --evidence-path docs/changes/can-fd-bringup/verify-report.md --layer Workflow --artifact verify-report
```

注意事项：

- 必须按 `propose -> apply -> verify -> review -> archive` 顺序推进。
- `review` 只接受 `verified` 状态。
- `archive` 默认只接受 `review-passed` 状态。
- `proposal.md` 需补全单问题、充分性、边界、重复性与 breaking change 检查项。

## 6. 发布与维护

常用维护入口：

```bash
bash scripts/health-check.sh
bash scripts/backup-rollback.sh list
bash scripts/devkit.sh benchmark run --iterations 5 --summary-json
bash scripts/devkit.sh security check --summary-json
bash scripts/devkit.sh eval run --suite deterministic --summary-json
bash scripts/devkit.sh release check
bash scripts/devkit.sh release build --out dist
bash scripts/version-manager.sh current
```

版本身份以 Manifest、锁与 Git 为事实源；已退役 `version-manager.sh unlock`，受控更版继续走 `upgrade --target ... --force`。档案 restore/rollback 需使用 CPython 3.12 构建环境，backup/list/verify 不需要 Python。该脚本不得用作 Root 或 live 用户目录恢复。

团队仓库接入或季度复核时，可先生成 Harness readiness 基线：

```bash
bash scripts/devkit.sh harness readiness --root /path/to/team-repo --output /tmp/harness-readiness.md
bash scripts/devkit.sh harness readiness --root /path/to/team-repo --gate --summary-json
bash scripts/devkit.sh harness readiness --root /path/to/team-repo --as-of 2026-07-18 --summary-json
```

`--as-of` 只用于可复现的 report-only 分析；`--gate` 强制使用当天并拒绝显式日期，防止历史评估时钟绕过 freshness。

先以 report-only 识别 evidence gap；只有团队明确了 owner、freshness 窗口内的验证日期和适用边界后，才把 `--gate` 接入 CI。MCP 存在时还要在 readiness metadata 中结构化声明只读、审批和凭证来源；仅有关键词说明不能替代权限合同。MCP 不适用时保持 `not-applicable`，不要为了“完整度”接入无用外部工具。

发布前最小检查：

```bash
bash scripts/devkit.sh validate --strict
bash scripts/check-runtime-boundary.sh
bash scripts/check-official-docs-governance.sh --summary-json
bash scripts/devkit.sh security check --summary-json
bash scripts/devkit.sh release check --summary-json
bash scripts/devkit.sh test
```

若启用 MCP、plugin、hook 或 automation，需要额外满足：

- `docs/runbooks/mcp-governance.md` 的准入门禁。
- `templates/security/tool-call-policy.md` 的工具调用策略。
- 只读优先、report-only 默认、写操作显式审批、可禁用和可回滚。

## 7. 回滚

回滚原则：

1. 先确认 install receipt、导出清单、发布记录或备份路径。
2. 不直接删除目标运行目录。
3. 回滚后执行目标工具的健康检查和 ADK 自身回归。
4. 在变更工件或 session summary 中记录回滚原因、命令和结果。

## 8. 参考资料吸收

吸收 Claude Code、Codex、TRAE、OpenClaw、OpenAI Developers 或其他平台教程时：

1. 先做字段映射和边界拆分。
2. 保留平台名作为来源 metadata。
3. 把可迁移项改写成平台中立的 ADK contract。
4. 对不可迁移项记录拒绝原因或保留为 reference，不进入 core。
