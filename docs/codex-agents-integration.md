# `~/codex`、`~/.codex/AGENTS.md` 与 adk 配合指南

## 1. 结论

`~/codex` 是本机 Codex CLI 的声明式资产仓库，`~/.codex/AGENTS.md` 是运行时策略层，adk 是 Agent/Skill/Profile 资产供应层。三者应协同，不应互相覆盖。

推荐方式：

- adk 负责校验并导出 Codex 格式 Agent/Skill/Profile 资产。
- `~/codex` 负责接收 adk 资产，注册到源资产和 manifest，执行 build/doctor/apply。
- `~/.codex/AGENTS.md` 负责规定何时使用这些 Agent/Skill，以及全局命令、验证、沟通和安全边界。
- adk 更新后，不自动覆盖 `~/codex` 或 `~/.codex/AGENTS.md`。
- 若需要新增 adk 配合规则，应先进入 `~/codex` 源资产，再执行 `~/codex` build/apply 与 `check-global-codex-health`。

## 2. 职责边界

| 层级 | 职责 | 更新方式 |
|---|---|---|
| `agent-dev-kit/manifest.yaml` | Agent/Skill/Profile 单一事实源 | 修改后跑 `validate --strict` 与 `test` |
| `agent-dev-kit/agents` | 角色 Agent 源资产 | 通过 adk convert 导出 |
| `agent-dev-kit/skills` | 默认技能源资产 | 通过 adk convert 导出 |
| `agent-dev-kit/optional-skills` | 按需技能源资产 | 用 `--with-optional-skill` 导出 |
| `~/codex/src/codex-home` | Codex Home 源资产 | 由 `~/codex` 侧注册和维护 |
| `~/codex/manifests` | profile、skill、agent、workflow 声明式关系 | 修改后跑 `~/codex/scripts/doctor.sh` |
| `~/.codex/agents` | 生产运行 Agent | 由 `~/codex/scripts/apply.sh` 写入 |
| `~/.codex/skills` | 生产运行 Skill | 由 `~/codex/scripts/apply.sh` 写入 |
| `~/.codex/AGENTS.md` | 全局代理行为规则 | 通过 `~/codex` 源资产维护，不由 adk 覆盖 |

## 3. 推荐交接组合

```bash
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh convert --target codex --profile personal-core --extra-profile release-hardening --with-optional-skill adk-planning-execution-loop --with-optional-skill adk-skill-composition-governance --with-optional-skill adk-security-supply-chain --with-optional-skill adk-cross-team-handoff --codex-profile team-collab --out ../reports/adk-codex-handoff --clean"
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh codex-handoff --codex-root ~/codex"
rtk bash -lc "cd ~/codex && rtk bash scripts/build.sh --profile team-collab"
rtk bash -lc "cd ~/codex && rtk bash scripts/doctor.sh --scope all"
rtk bash -lc "cd ~/codex && rtk bash scripts/apply.sh --profile team-collab --dry-run"
rtk ../scripts/check-global-codex-health.sh ~/.codex minimal
```

说明：

- `personal-core`：个人生产默认研发能力。
- `release-hardening`：发布、可靠性、安全强化。
- `adk-runtime-router`：adk-first 运行时技能路由裁决。
- `adk-test-strategy`：通用测试策略与 TDD 分级。
- `adk-code-review-loop`：独立代码审查与反馈修复闭环。
- `adk-parallel-agent-governance`：并行子代理任务包、冲突矩阵和整合验证。
- `adk-worktree-governance`：git worktree 隔离开发治理。
- `adk-branch-closeout`：开发分支收尾、PR、保留和清理决策。
- `adk-planning-execution-loop`：长任务计划与恢复。
- `adk-skill-composition-governance`：多技能组合治理。
- `adk-security-supply-chain`：第三方资产引入审查。
- `adk-cross-team-handoff`：团队交接。
- `adk-artifact-gating`：高风险变更证据门禁。

说明：`../reports/adk-codex-handoff` 是交接目录，不是最终运行目录。目录内必须使用 `src/codex-home/vendor/...` 与 `manifest-fragments/*.json` 形态；正式生效前必须在 `~/codex` 中合并来源、profile 绑定和 apply plan。

## 4. `~/.codex/AGENTS.md` 建议追加小节

以下内容适合作为 `~/.codex/AGENTS.md` 的附加小节。不要替换个人原有规则。

```md
## agent-dev-kit 配合规则

- `agent-dev-kit` 是嵌入式全栈开发 Agent/Skill/Profile 的生产资产来源，覆盖芯片/板级约束、启动链、BSP、OS/runtime、驱动、组件、设备应用、上位机/产测/诊断工具、构建调试、验证、发布、量产和现场维护。
- adk 只负责提供经过验证且符合 `~/codex` 规范的 vendor 源资产与 manifest fragments，不覆盖本文件。
- 不手工把参考仓资产或 adk 导出物直接复制进 `~/.codex/agents` 或 `~/.codex/skills`。
- adk 资产更新必须先在 `llm_agent/agent-dev-kit` 通过 `tests/run_all.sh`，再交给 `~/codex` 注册、build、doctor 和 apply。
- 生产可用结论必须附 `llm_agent/scripts/check-adk-harden-readiness.sh . --require-pilot` 证据。
- fallback 下线或替代结论必须附 `agent-dev-kit/scripts/check-fallback-sunset.sh` 与 `agent-dev-kit/scripts/pilot-readiness.sh --summary-json` 证据；需要归档时附 `--score-tsv` 输出。`planned` pilot 不能作为下线依据。
- 涉及 `~/.codex` 运行目录时，必须附 `~/codex` build/apply 证据与 `llm_agent/scripts/check-global-codex-health.sh ~/.codex minimal` 证据。

### adk Skill 路由

- 任务开始前需要选择技能、判定 fallback：优先 `adk-runtime-router`。
- 通用测试策略、TDD、回归测试：优先 `adk-test-strategy`。
- 独立代码审查、review 反馈修复、复审：优先 `adk-code-review-loop`。
- 并行子代理调度：优先 `adk-parallel-agent-governance`。
- worktree 隔离开发：优先 `adk-worktree-governance`。
- 开发完成后的合并、PR、保留或丢弃：优先 `adk-branch-closeout`。
- 长任务、跨会话恢复、复杂计划执行：优先 `adk-planning-execution-loop`。
- 多技能触发冲突、profile 组合、fallback 判定：优先 `adk-skill-composition-governance`。
- 量产、产测、烧录、诊断、OTA、回滚和现场维护：优先 `adk-production-field-readiness`。
- 第三方 skill、agent、脚本、参考资产引入前：必须使用 `adk-security-supply-chain`。
- 跨团队交接、Owner 变更、签收复验：使用 `adk-cross-team-handoff`。
- 高风险变更、共享契约、发布链路：使用核心 `adk-artifact-gating`。
- 完成、提交、发布、可用性声明前：必须使用 `adk-verification-before-completion`。
```

## 5. 不建议写入 `~/.codex/AGENTS.md` 的内容

- 参考仓全文分析。
- 一次性 pilot 报告。
- adk 的完整 Agent/Skill 正文。
- 安装报告、备份路径历史列表。
- 需要频繁变化的 adoption matrix 明细。
- 任何密钥、账号、私有业务上下文。

这些内容应保留在 `llm_agent/reports`、`subrepos/adoption-matrix.md` 或 adk 源文档中。

## 6. 更新流程

### 6.1 只更新 adk 源资产

```bash
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh test"
```

### 6.2 交接到 `~/codex` 并预览 apply

```bash
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh convert --target codex --profile personal-core --extra-profile release-hardening --with-optional-skill adk-planning-execution-loop --with-optional-skill adk-skill-composition-governance --with-optional-skill adk-security-supply-chain --with-optional-skill adk-cross-team-handoff --codex-profile team-collab --out ../reports/adk-codex-handoff --clean"
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh codex-handoff --codex-root ~/codex"
rtk bash -lc "cd ~/codex && rtk bash scripts/build.sh --profile team-collab"
rtk bash -lc "cd ~/codex && rtk bash scripts/apply.sh --profile team-collab --dry-run"
rtk ../scripts/check-global-codex-health.sh ~/.codex minimal
```

### 6.3 修改 `~/.codex/AGENTS.md`

修改后至少运行：

```bash
rtk ../scripts/check-global-codex-health.sh ~/.codex minimal
```

若修改影响 adk 生产结论，继续运行：

```bash
rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot
```

## 7. 冲突处理

| 冲突 | 处理方式 |
|---|---|
| `~/.codex/AGENTS.md` 规则与 adk skill 触发冲突 | 以 `~/.codex/AGENTS.md` 为运行时优先级，并回灌 `~/codex` 与 adk routing 文档 |
| 多个 skill 同时像主技能 | 先用 `adk-runtime-router` 裁决 primary/supporting/fallback；复杂组合再叠加 `adk-skill-composition-governance` |
| optional skill 越来越多导致触发噪音 | 调整 profile 或减少默认安装 optional skill |
| 参考仓资产想直接进入生产 | 先走 `adk-security-supply-chain` + adoption matrix + adk 门禁，再进入 `~/codex` |
| apply 后行为异常 | 使用 `~/codex` apply plan 或 backup 回滚，并记录报告 |

## 8. 验收标准

可以声明 `~/codex`、`~/.codex/AGENTS.md` 与 adk 配合健康，必须满足：

```bash
rtk bash -lc "cd ~/codex && rtk bash scripts/doctor.sh --scope all"
rtk ../scripts/check-global-codex-health.sh ~/.codex minimal
rtk ../scripts/check-runtime-routing.sh .
rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot
```

若任一命令失败，只能声明“已更新文档/配置，尚未生产放行”。
