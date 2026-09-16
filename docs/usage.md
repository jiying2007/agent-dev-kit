# Usage

`agent-dev-kit` 是通用 ADK 资产包。它维护 Agent、Skill、Profile、Workflow 和治理契约，并通过显式 direct `tool_targets` 导出到不同运行时；需要外部声明式链路承接的运行体系进入 `external_handoff_targets`，core 不绑定任何单一平台。

完整使用指南见 `docs/adk-usage-guide.md`；本文保留为常用命令速查。

发布支持环境为 Python 3.11+，固定运行依赖为 `PyYAML==6.0.3` 与 `jsonschema==4.26.0`。发布前安装 `.[quality]` 并执行 Ruff 与 pip-audit；工具缺失或审计源不可用时不得声称质量门禁通过。

升级现有自定义 manifest 时，先执行 `bash scripts/devkit.sh validate --strict`。关键 nested object 已改为 typed schema，旧的未知扩展字段、字符串冒充数组/布尔值以及缺失必填项会 fail closed；应按 `manifests/manifest.schema.json` 迁移。确需保留的产品级扩展元数据应移动到顶层 `x-<name>` namespace，不能通过放宽核心 schema 保留未声明行为。

## 1. 预检查

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh validate --quick
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh asset-taxonomy
bash scripts/devkit.sh official-docs-governance --summary-json
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
PATH=/usr/bin:/bin bash scripts/validate-assets.sh --strict
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
| `openspec-driven` | Spec 驱动变更 |
| `large-refactor` | 大型重构 |
| `incident-response` | 事故响应 |
| `research-intake` | 参考资料吸收 |

Profile 继承一致性检查：

```bash
bash scripts/check-profile-coherence.sh
```

## 3. 安装和导出

安装通过 plan/apply/receipt/rollback 事务把 Agent/Skill 复制到显式 target。plan 会阻断未托管冲突和过期/漂移输入；`symlink` 模式未实现并会 fail closed：

```bash
bash scripts/devkit.sh install plan --tool claude-code --target /tmp/adk-claude-target --mode copy --profile core --extra-profile release-hardening --output /tmp/adk-plan.json
bash scripts/devkit.sh install apply --plan /tmp/adk-plan.json
bash scripts/devkit.sh install rollback --receipt /tmp/adk-claude-target/.adk-install-receipt.json
```

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
- `--out`：导出输出目录。
- `--clean`：导出前清理输出目录。
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
bash scripts/devkit.sh match --skill adk-planning-execution-loop --scope optional-skill --text "复杂任务需要计划审查和执行检查点时"
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
bash scripts/devkit.sh evidence append --file docs/changes/can-fd-bringup/negative-results.md --command "bash tests/run_all.sh" --exit-code 0 --summary "all tests passed" --evidence-path docs/changes/can-fd-bringup/verify-report.md --layer Workflow --artifact verify-report
```

注意事项：

- 必须按 `propose -> apply -> verify -> review -> archive` 顺序推进。
- `review` 只接受 `verified` 状态。
- `archive` 默认只接受 `review-passed` 状态。
- `proposal.md` 需补全单问题、充分性、边界、重复性与 breaking change 检查项。

## 6. 发布与维护

常用维护入口：

```bash
bash scripts/devkit.sh health
bash scripts/devkit.sh backup list
bash scripts/devkit.sh benchmark run --iterations 5 --summary-json
bash scripts/devkit.sh security check --summary-json
bash scripts/devkit.sh eval run --suite deterministic --summary-json
bash scripts/devkit.sh release check
bash scripts/devkit.sh release build --out dist
bash scripts/devkit.sh version show
```

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
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh official-docs-governance --summary-json
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
