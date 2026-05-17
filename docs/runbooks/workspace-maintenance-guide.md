# llm_agent 工作区维护与脚本指南

## 1. 定位

`llm_agent` 是 adk 的上游治理工作区，负责三件事：

1. 管理参考子仓清单与同步策略。
2. 从参考子仓提炼可采纳实践，并记录采纳/观察/拒绝原因。
3. 推动 `agent-dev-kit` 落地、验证、交接到 `~/codex`，再由 `~/codex` apply 到 `~/.codex` 并把真实运行结果回灌。

不推荐在 `llm_agent` 中直接改 `~/.codex` 运行资产。生产运行资产应先由 adk 导出，再进入 `~/codex` 的源资产和 manifest 治理链路，最后由 `~/codex/scripts/apply.sh` 注入 `~/.codex`。

## 2. 目录职责

| 路径 | 职责 | 维护要求 |
|---|---|---|
| `AGENTS.md` | 工作区全局规则、参考子仓总览、维护记录 | 规则或流程变化时同步更新 |
| `subrepos/registry.csv` | 参考子仓单一清单 | 新增/禁用子仓必须更新 |
| `subrepos/adoption-matrix.md` | 候选采纳矩阵 | 每个候选必须有决策、状态、目标层和证据 |
| `subrepos/phase-gate.env` | 是否允许追踪上游更新 | 默认先压实 adk，再开门同步 |
| `scripts/` | 治理、同步、门禁脚本 | 新脚本必须写入 `scripts/README.md` |
| `reports/` | pilot、安装、周报、wave 记录 | 生产结论必须有报告证据 |
| `agent-dev-kit/` | adk 源资产与测试 | 所有生产能力最终在这里压实 |

## 3. 维护流程

### 3.1 日常健康检查

```bash
rtk scripts/check-doc-sync.sh .
rtk scripts/check-runtime-routing.sh .
rtk scripts/check-upstream-intake-readiness.sh .
rtk ../scripts/check-global-codex-health.sh ~/.codex minimal
```

适用场景：只确认当前状态是否健康，不同步参考仓，不部署。

### 3.2 adk 压实检查

```bash
rtk ../scripts/check-adk-harden-readiness.sh .
```

适用场景：修改了 adk 文档、profile、skill、agent、workflow 或 root scripts 后，需要确认基础门禁。

### 3.3 生产级放行检查

```bash
rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot
```

适用场景：准备声明 adk 可进入 `~/codex` 生产分发链路，或准备由 `~/codex` 重新 apply 到 `~/.codex`。

该门禁会检查：

- adk strict validation
- optional skills 回归
- 外部仓库引用隔离
- skill metadata
- skill routing conflicts
- docs sync
- adoption matrix 状态
- observe backlog / delivery adopt 深度
- runtime routing
- upstream intake readiness
- adk full regression suite
- codex pilot evidence
- codex pilot coverage
- `~/codex` build/apply 证据与 global `~/.codex` health

### 3.4 参考子仓同步

同步前先跑：

```bash
rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot
```

同步和扫描：

```bash
rtk scripts/sync-subrepos.sh . fetch
rtk scripts/diff-scan.sh . 7 reports/weekly-change-report.md
```

若门禁未开，脚本会阻止同步。不要用 `--force` 常态绕过，除非只是一次性紧急扫描并会在报告里说明原因。

### 3.5 候选吸收

1. 在 `subrepos/adoption-matrix.md` 增加候选行。
2. 给出 `adopt/observe/reject`。
3. 对 `adopt + done`，必须有本地证据路径。
4. 对 delivery 类 adopt，必须覆盖 Agent/Skill/Workflow 至少一层。
5. 对安全、脚本、第三方资产，先走 `security-supply-chain`。
6. 最终执行：

```bash
rtk scripts/check-adoption-matrix-status.sh .
rtk scripts/check-upstream-intake-readiness.sh .
rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot
```

## 4. adk 变更分级

| 变更类型 | 最小验证 | 说明 |
|---|---|---|
| 文档说明 | `rtk scripts/check-doc-sync.sh .` | 若涉及 adk docs，还应跑 adk 相关测试 |
| runbook / workflow 文档 | `rtk agent-dev-kit/tests/run_all.sh` | 防止 catalog、格式、引用漂移 |
| Agent/Skill 内容 | `rtk agent-dev-kit/tests/run_all.sh` | 会覆盖 frontmatter、内容质量、触发矩阵 |
| profile / manifest | `rtk agent-dev-kit/tests/test_profile_coherence.sh` + `rtk agent-dev-kit/tests/run_all.sh` | 防止继承重复与未知引用 |
| install / convert 脚本 | `rtk agent-dev-kit/tests/run_all.sh` | 必须覆盖安装、转换、dry-run |
| root 门禁脚本 | `rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot` | 影响生产放行链路 |
| `~/codex -> ~/.codex` 部署 | `rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot` + `~/codex` apply plan / dry-run / health 证据 | 必须保留 backup |

## 5. 生产部署流程

生产部署不从 `agent-dev-kit` 直接写入 `~/.codex`。adk 只负责校验并导出；`~/codex` 负责注册、构建、预览和注入。

```bash
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh validate --strict"
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh convert --target codex --profile personal-core --extra-profile release-hardening --with-optional-skill adk-planning-execution-loop --with-optional-skill adk-skill-composition-governance --with-optional-skill adk-security-supply-chain --with-optional-skill adk-cross-team-handoff --codex-profile team-collab --out ../reports/adk-codex-handoff --clean"
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh codex-handoff --codex-root ~/codex"
rtk bash -lc "cd ~/codex && rtk bash scripts/build.sh --profile team-collab"
rtk bash -lc "cd ~/codex && rtk bash scripts/plan.sh --target ~/.codex --output build/apply-plan.json"
rtk bash -lc "cd ~/codex && rtk bash scripts/apply.sh --profile team-collab --dry-run"
rtk ../scripts/check-global-codex-health.sh ~/.codex minimal
rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot
```

生产安装纪律：

- adk 导出物只作为交接输入，不直接作为 `~/.codex` 来源；产物必须符合 `~/codex` 的 `src/codex-home/vendor/...` 与 `manifest-fragments/*.json` 规范。
- `~/codex` 侧必须更新源资产与 manifest，并运行 build / doctor / apply dry-run。
- 真正写入 `~/.codex` 时由 `~/codex/scripts/apply.sh` 负责备份、覆盖策略和回滚计划。
- 使用 adk `manifest.yaml` 版本和 `~/codex` apply plan 双重记录，防止误装不匹配版本。
- 安装后必须跑 `check-global-codex-health.sh`。

## 6. 回滚流程

先从安装报告确认备份路径，例如：

```text
$HOME/.codex/.adk-backups/YYYYMMDDTHHMMSSZ
```

回滚原则：

1. 不直接删除 `~/.codex`。
2. 先确认备份中存在 `agents/` 与 `skills/`。
3. 回滚后执行健康检查。
4. 在 `reports/` 新增回滚记录。

建议由用户明确授权后再执行回滚，因为会覆盖生产运行目录。

## 7. `~/.codex/AGENTS.md` 与 adk 的关系

`~/codex` 是 Codex Home 的声明式资产仓库，`~/.codex/AGENTS.md` 是运行时总策略层，adk 是 Agent/Skill/Profile 资产供应层。三者不要互相替代。

推荐职责边界：

| 层级 | 放什么 | 不放什么 |
|---|---|---|
| `~/.codex/AGENTS.md` | 全局行为规则、命令硬约束、沟通风格、流程升级/降级、技能路由总原则 | 大量具体 Agent/Skill 正文、参考仓细节、一次性试跑报告 |
| `~/codex/src/codex-home` + `~/codex/manifests` | 经治理的 Codex Home 源资产与声明式关系 | 未登记来源、未审查第三方资产 |
| `~/.codex/agents/` | `~/codex` apply 后的运行 Agent | 手工复制的第三方 Agent |
| `~/.codex/skills/` | `~/codex` apply 后的运行 Skill + 系统保留 skill | 未审查第三方技能 |
| `llm_agent/agent-dev-kit` | 源资产、测试、profile、runbook、导出物 | 生产运行时的临时状态 |
| `llm_agent/reports` | 安装、pilot、回归、上游吸收证据 | 密钥或私人业务数据 |

`~/.codex/AGENTS.md` 建议保留这些与 adk 配合的规则：

```md
## agent-dev-kit 配合规则

- `agent-dev-kit` 是嵌入式系统开发 Agent/Skill/Profile 的生产资产来源。
- 不手工把参考仓资产或 adk 导出物直接复制进 `~/.codex/agents` 或 `~/.codex/skills`。
- adk 资产更新必须先在 `llm_agent/agent-dev-kit` 通过回归，再交给 `~/codex` 注册、build、doctor 和 apply。
- 长任务优先使用 `planning-execution-loop`。
- 多技能冲突时以 `skill-composition-governance` 判定 primary/supporting/fallback。
- 第三方技能、脚本或参考资产进入全局环境前必须使用 `security-supply-chain`。
- 完成前必须使用 `verification-before-completion` 核对证据。
- 涉及 `~/.codex` 生产可用性结论时，必须同时附 `~/codex` build/apply 证据和 `check-global-codex-health.sh ~/.codex minimal` 证据。
```

当前不建议让 adk 覆盖 `~/.codex/AGENTS.md`，也不建议绕过 `~/codex` 直接写入 `~/.codex`。原因：

- `AGENTS.md` 包含个人环境硬约束，如 `rtk` 命令前缀、沟通偏好、文档目录、并行策略。
- `~/codex` 负责 Codex Home 源资产、manifest、build、apply 和 drift 管理。
- adk 的职责是提供经过门禁压实的上游资产，不是替换个人全局策略或运行目录管理器。
- 若要把 adk 的策略沉淀进 `~/.codex/AGENTS.md`，应先进入 `~/codex` 源资产，再采用"追加小节 + 人工审阅 + 健康检查"的方式。

## 8. 常见问题

### 8.1 是否可以跳过 pilot？

开发中可以临时不加 `--require-pilot`，但不能据此声明生产可用。生产结论必须使用：

```bash
rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot
```

### 8.2 是否可以直接更新参考子仓？

可以同步，但必须先确认 phase gate。默认策略是先压实 adk，再追踪更新。

### 8.3 为什么 observe 已清零还要跑 observe 检查？

因为脚本会确认 backlog cleared，防止后续新增 observe 后没有三层证据。

### 8.4 adk 能否替代所有参考仓？

当前 adk 是生产分发层和压实层，不是参考仓全文镜像。参考仓继续作为上游灵感和候选池；只有经过采纳矩阵、adk 实现、门禁和 pilot 的能力才进入生产。

---

## 9. 脚本参考手册

> 本节汇总所有治理脚本的入口、门禁含义与常用参数。

### 9.0 Registry 字段约定（v1）

`subrepos/registry.csv` 统一使用以下列：

```csv
repo,group,priority,sync_mode,branch,enabled,notes,status,owner,last_reviewed_on,intake_policy
```

- `status`：`active` / `disabled`
- `owner`：治理责任方
- `last_reviewed_on`：最近复审日期（`YYYY-MM-DD`）
- `intake_policy`：吸收策略（如 `adopt-first`、`observe-first`、`selective-adopt`、`pilot-first`）

### 9.1 阶段门禁（先压实 adk）

默认策略：先压实 `agent-dev-kit`，再跟踪外部子仓更新。

门禁文件：`subrepos/phase-gate.env`（默认 `allow_upstream_sync=no`）。

```bash
# 先做压实检查（严格校验 + 可选技能回归 + 外部引用门禁）
scripts/check-adk-harden-readiness.sh .

# 通过后自动开门（可选）
scripts/check-adk-harden-readiness.sh . --open-gate

# 要求 codex 试跑证据也必须就绪（更严格）
scripts/check-adk-harden-readiness.sh . --require-pilot
scripts/check-adk-harden-readiness.sh . --require-pilot --open-gate

# 若临时不检查全局 ~/.codex 健康（不建议）
scripts/check-adk-harden-readiness.sh . --skip-global-codex-check

# 若临时跳过 adk 全量回归（不建议）
scripts/check-adk-harden-readiness.sh . --skip-full-suite

# 显式打开/跳过各类检查（默认已开启）
scripts/check-adk-harden-readiness.sh . --check-skill-metadata --check-routing-conflicts --check-doc-sync
scripts/check-adk-harden-readiness.sh . --skip-skill-metadata-check --skip-routing-conflicts-check --skip-doc-sync-check
scripts/check-adk-harden-readiness.sh . --check-matrix-status --check-observe-intake-depth --check-delivery-adopt-depth
scripts/check-adk-harden-readiness.sh . --check-runtime-routing --check-pilot-coverage --check-upstream-intake
```

若未开门，`sync-subrepos.sh` / `diff-scan.sh` 会返回 `[BLOCK]`。
紧急一次性绕过：追加 `--force`（建议仅临时使用并留痕）。

### 9.2 Codex Pilot 检查

```bash
# 完整检查（默认模式：evidence + coverage + 场景验证）
scripts/check-codex-pilot.sh .

# 只检查基础证据字段
scripts/check-codex-pilot.sh . evidence

# 只检查覆盖字段
scripts/check-codex-pilot.sh . coverage

# 完整检查（等价于默认模式）
scripts/check-codex-pilot.sh . full
```

当 `pilot_full_coverage_ready=yes` 时，`coverage` 和 `full` 模式会强制校验六类场景字段、场景章节、`ImplementationPlan/ReviewReport/TestReport` artifact 标签与命令级 Evidence Index。

> **旧脚本兼容提示**：`check-codex-pilot-evidence.sh` 和 `check-codex-pilot-coverage.sh` 已标记为弃用，会自动转发到新脚本。

### 9.3 其他门禁检查脚本

```bash
# 全局 ~/.codex 健康检查
scripts/check-global-codex-health.sh ~/.codex minimal

# 技能元数据检查
scripts/check-skill-metadata.sh .

# 技能路由冲突检查
scripts/check-skill-routing-conflicts.sh .

# 文档与治理文件同步检查
scripts/check-doc-sync.sh .

# adoption-matrix 状态检查
scripts/check-adoption-matrix-status.sh .

# observe 吸收深度检查
scripts/check-observe-intake-depth.sh .

# delivery 采纳深度检查
scripts/check-delivery-adopt-depth.sh .

# 生产级 runtime routing 资产检查
scripts/check-runtime-routing.sh .

# 上游吸收生产准入检查
scripts/check-upstream-intake-readiness.sh .

# 全局 codex 目标策略校验
scripts/check-global-codex-target-policy.sh [WORKSPACE_ROOT]
```

`check-runtime-routing.sh` 会同时调用 `agent-dev-kit/scripts/check-profile-coherence.sh`，防止 profile 继承后重复声明 Agent/Skill 或引用漂移。

### 9.4 同步子仓增量

```bash
scripts/sync-subrepos.sh . fetch
scripts/sync-subrepos.sh . pull
scripts/sync-subrepos.sh . fetch --force
```

- `fetch`：对启用子仓执行 `git fetch --all --prune`
- `pull`：仅对 `registry.csv` 中 `sync_mode=pull` 的子仓执行 `git pull --ff-only`

### 9.5 扫描高价值变更

```bash
scripts/diff-scan.sh . 7 reports/weekly-change-report.md
scripts/diff-scan.sh . 7 reports/weekly-change-report.md --force
```

- 参数 2：扫描最近 N 天（默认 `7`）
- 参数 3：报告输出路径（默认 `reports/weekly-change-report.md`）

冻结后一键巡检：

```bash
scripts/run-post-freeze-cycle.sh .
scripts/run-post-freeze-cycle.sh . 7 reports/weekly-change-report.md
```

adoption-matrix 汇总报告生成脚本：

```bash
scripts/generate-adoption-matrix-summary.sh .
scripts/generate-adoption-matrix-summary.sh . reports/adoption-matrix-summary.md
```

### 9.6 检查 AGENTS 覆盖

```bash
scripts/check-agents-coverage.sh .
```

检查项：子仓是否存在本地 `AGENTS.md`、根 `AGENTS.md` 是否包含子仓名称。

### 9.7 新仓库接入

```bash
scripts/new-repo-onboard.sh <repo-path> [--adopt|--observe|--selective|--pilot]
```

功能：自动注册到 `registry.csv`、生成/追加仓库 `AGENTS.md`、更新 `adoption-matrix.md`、运行基础检查、生成接入报告到 `reports/`。

详细流程参见：`docs/runbooks/new-repo-onboarding.md`

### 9.8 备份回滚

```bash
scripts/backup-rollback.sh [ACTION] [OPTIONS]
```

功能：`backup`（创建完整备份快照）、`rollback`（从备份恢复）、`list`（列出可用备份点）、支持自动清理过期备份。

### 9.9 一键门禁检查

```bash
# 运行所有 check-* 脚本并汇总结果
scripts/check-all.sh

# 快速模式（跳过耗时的 check-adk-harden-readiness.sh）
scripts/check-all.sh --quick

# 详细模式（显示每个脚本的完整输出）
scripts/check-all.sh --verbose

# 组合使用
scripts/check-all.sh --quick --verbose
```

功能：自动发现 `scripts/check-*.sh` 并逐个运行、记录 PASS/FAIL 状态、输出汇总表、`--quick` 跳过耗时脚本、全部通过返回 0。

### 9.10 统一入口 devkit.sh

```bash
scripts/devkit.sh help              # 查看帮助
scripts/devkit.sh check --quick     # 一键门禁（快速）
scripts/devkit.sh check --full      # 一键门禁（完整）
scripts/devkit.sh onboard <repo>    # 新仓库接入
scripts/devkit.sh sync fetch        # 子仓同步
scripts/devkit.sh diff              # 差异扫描（默认 7 天）
scripts/devkit.sh diff 14           # 差异扫描（14 天）
scripts/devkit.sh health            # 健康检查
scripts/devkit.sh weekly-report     # 生成周报
scripts/devkit.sh cleanup --dry-run # 清理过期报告（预览）
scripts/devkit.sh cleanup           # 清理过期报告（执行）
```

### 9.11 工作区健康检查

```bash
scripts/health-check.sh check-all --root .
scripts/health-check.sh .
```

功能：综合健康检查（目录结构完整性、关键文件存在性、registry 格式、依赖、门禁入口、脚本语法），输出通过/失败/警告三级状态报告。

### 9.12 版本管理

```bash
scripts/version-manager.sh [ACTION] [OPTIONS]
```

功能：`check`（检查当前版本状态）、`lock`（锁定版本号）、`upgrade`（执行版本升级并验证），支持版本回退和变更日志生成。

### 9.13 自动生成周报

```bash
scripts/generate-weekly-report.sh [WORKSPACE_ROOT] [--output <path>]
```

功能：自动汇总最近 7 天 git 提交摘要、读取子仓同步状态、统计 adoption-matrix 决策分布、运行质量门禁快速检查、输出报告到 `reports/weekly-report-YYYY-MM-DD.md`。

建议配合 cron 定时执行：
```bash
# 每周五下午 6 点自动生成周报
0 18 * * 5 cd /path/to/llm_agent && rtk scripts/generate-weekly-report.sh .
```

### 9.14 清理归档旧报告

```bash
scripts/cleanup-reports.sh [WORKSPACE_ROOT] [--dry-run] [--days N]
```

功能：将 `reports/` 中超过指定天数的 `.md` 报告移入 `reports/archive/`，保留 `.template.md` 模板文件。默认 30 天。

### 9.15 安装 Pre-commit Hook

```bash
scripts/install-pre-commit-hook.sh [WORKSPACE_ROOT]
```

功能：安装 git pre-commit hook，自动备份已有 hook。

hook 检查项：
1. **Shell 脚本语法**：对 `scripts/*.sh` 及暂存区中的 `.sh` 文件执行 `bash -n`。
2. **AGENTS.md 引用文件**：检查引用的文件是否存在。
3. **registry.csv 格式**：校验表头、列数、字段值。

跳过 hook：`git commit --no-verify`。卸载 hook：`rm .git/hooks/pre-commit`。

---

## 10. 维护记录模板

```md
### YYYY-MM-DD（主题）
- 变更范围：
- 触发原因：
- 更新条目：
- 验证命令：
- 验证结果：
- 后续事项：
```
