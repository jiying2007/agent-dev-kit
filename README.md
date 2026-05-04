# Global Dev Kit

`global-dev-kit`（gdk）是面向 `~/.codex` 等开发代理运行目录的 Agent/Skill/Profile 生产资产包。它的目标是把参考仓中的优秀方法论压实为可安装、可验证、可回滚、可持续迭代的工程资产。

当前版本：`0.3.0`。

## 1. 核心定位

gdk 不是参考仓集合，也不是直接替换 `~/.codex/AGENTS.md` 的全局策略文件。它负责：

1. 维护 Agent/Skill/Profile 单一事实源：`manifest.yaml`。
2. 提供安装、转换、匹配、catalog、workflow、evidence 命令。
3. 用测试和门禁压实 Agent/Skill/Workflow/runbook。
4. 把稳定资产安装到 `~/.codex/agents` 与 `~/.codex/skills`。
5. 为真实生产使用提供安装报告、备份、pilot 与健康检查证据。

## 2. 当前资产概览

- Agents：10 个角色 Agent。
- Core Skills：22 个稳定技能。
- Optional Skills：7 个可选技能。
- Profiles：`core`、`personal-core`、`embedded-fullstack`、`release-hardening`、`artifact-gated-lite`、`team-core`、`openspec-driven`、`large-refactor`、`incident-response`、`research-intake`。
- Tool Targets：`codex`、`claude-code`、`hermes-agent`、`opencode`。

## 3. 目录结构

| 路径 | 作用 |
|---|---|
| `manifest.yaml` | Agent/Skill/Profile/tool target 单一事实源 |
| `agents/` | 角色化 Agent 定义 |
| `skills/` | 默认可安装技能 |
| `optional-skills/` | 按需安装技能 |
| `scripts/` | 安装、转换、验证、catalog、workflow、evidence 脚本 |
| `tests/` | 全量回归与 smoke 测试 |
| `docs/` | 使用指南、命令说明、workflow、runbook、生产配合说明 |
| `docs/runbooks/` | 场景化生产操作手册 |

## 4. 快速验证

在 `llm_agent` 工作区中执行命令时必须使用 `rtk` 前缀：

```bash
rtk bash -lc "cd global-dev-kit && bash scripts/devkit.sh validate --strict"
rtk bash -lc "cd global-dev-kit && bash scripts/devkit.sh test"
```

若已在 `global-dev-kit` 目录内，普通环境可直接执行：

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh test
```

## 5. 生产安装到 `~/.codex`

推荐安装组合：

- 主 profile：`personal-core`
- 叠加 profile：`release-hardening`
- optional skills：`planning-execution-loop`、`skill-composition-governance`、`security-supply-chain`、`cross-team-handoff`、`artifact-gated-lite`

命令：

```bash
rtk bash -lc "cd global-dev-kit && bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile personal-core --extra-profile release-hardening --with-optional-skill planning-execution-loop --with-optional-skill skill-composition-governance --with-optional-skill security-supply-chain --with-optional-skill cross-team-handoff --with-optional-skill artifact-gated-lite --backup --install-report ../reports/gdk-install-report-$(date +%F).md --lock-version 0.3.0"
rtk scripts/check-global-codex-health.sh ~/.codex minimal
rtk scripts/check-gdk-harden-readiness.sh . --require-pilot
```

生产纪律：

- 使用 `copy`，不使用 `symlink`，避免工作区变动影响运行目录。
- 使用 `--backup`，安装前备份 `~/.codex/agents` 与 `~/.codex/skills`。
- 使用 `--install-report`，记录安装证据。
- 使用 `--lock-version`，防止装错版本。
- 安装后必须运行全局健康检查。

## 6. Profile 选择

| Profile | 场景 | 说明 |
|---|---|---|
| `core` | 通用研发 | 最小稳定主干，覆盖需求、任务、接口、测试、调试、验证、PR 门禁 |
| `personal-core` | 个人 `~/.codex` 生产默认 | 在 `core` 基础上增加发布与 ADR 能力 |
| `embedded-fullstack` | 嵌入式全栈 | 默认 profile，覆盖驱动、组件、BSP、RTOS、构建、性能、发布 |
| `release-hardening` | 发布前强化 | 安全、可靠性、HIL/SIL、版本发布 |
| `artifact-gated-lite` | 高风险变更 | 复用 `core`，配合 optional skill 产出轻量 artifact 门禁 |
| `team-core` | 团队交付 | 责任矩阵、交接、复验、发布治理 |
| `openspec-driven` | Spec 驱动 | requirements/design/tasks 与 gdk workflow 对齐 |
| `large-refactor` | 大型重构 | API 稳定性、边界冻结、回归压实 |
| `incident-response` | 事故响应 | RCA、恢复、可靠性、安全复盘 |
| `research-intake` | 参考仓吸收 | 候选筛选、组合治理、供应链审查 |

Profile 继承和重复声明由以下脚本检查：

```bash
bash scripts/check_profile_coherence.sh
```

该检查已纳入 `bash scripts/devkit.sh test`。

## 7. Optional Skills

| Optional Skill | 场景 |
|---|---|
| `test-flakiness-triage` | 测试波动定位 |
| `cross-team-handoff` | 跨团队交接 |
| `incident-rca-report` | 事故复盘 |
| `artifact-gated-lite` | 高风险 artifact 门禁 |
| `planning-execution-loop` | 长任务计划、检查点、恢复和收口 |
| `skill-composition-governance` | 主技能、辅助技能、fallback、弃用治理 |
| `security-supply-chain` | 第三方资产、脚本、技能引入前审查 |

安装 optional skill 示例：

```bash
bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile personal-core --with-optional-skill planning-execution-loop
```

## 8. 工作流命令

gdk 的变更工件按固定顺序推进：

```text
propose -> apply -> verify -> review -> archive
```

示例：

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

Evidence Index 字段固定为：

```md
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
```

## 9. 生产验证

gdk 源仓内最小验证：

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh test
```

`llm_agent` 工作区生产放行验证：

```bash
rtk scripts/check-gdk-harden-readiness.sh . --require-pilot
```

当前 `--require-pilot` 会校验 `reports/codex-pilot-report.md` 中六类场景：

- 新功能交付
- 缺陷修复
- 重构压实
- 发布收口
- 团队交接
- 上游吸收

边界：当前 pilot 是 gdk 自举 + 生产安装验证，真实业务长期样例仍需持续补充。

## 10. `~/.codex/AGENTS.md` 配合方式

详见 `docs/codex-agents-integration.md`。

原则：

- `~/.codex/AGENTS.md` 保留个人全局策略、命令硬约束和流程路由。
- gdk 安装 `agents/` 与 `skills/`，不覆盖 `~/.codex/AGENTS.md`。
- 若要把 gdk 策略加入 `~/.codex/AGENTS.md`，采用追加小节方式，不整体替换。
- 第三方参考仓资产必须先经过 gdk 审查和门禁，不直接进入 `~/.codex`。

## 11. 重要文档

- `docs/usage.md`：详细命令使用。
- `docs/commands.md`：命令索引。
- `docs/workflows.md`：场景工作流。
- `docs/runbooks/production-deployment.md`：生产部署。
- `docs/runbooks/runtime-routing.md`：运行路由。
- `docs/runbooks/upstream-intake.md`：上游吸收。
- `docs/codex-agents-integration.md`：`~/.codex/AGENTS.md` 配合指南。
