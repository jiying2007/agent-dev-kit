# `~/.codex/AGENTS.md` 与 gdk 配合指南

## 1. 结论

`~/.codex/AGENTS.md` 是运行时策略层，gdk 是 Agent/Skill/Profile 资产供应层。两者应协同，不应互相覆盖。

推荐方式：

- gdk 负责安装 `~/.codex/agents/` 与 `~/.codex/skills/`。
- `~/.codex/AGENTS.md` 负责规定何时使用这些 Agent/Skill，以及全局命令、验证、沟通和安全边界。
- gdk 更新后，不自动覆盖 `~/.codex/AGENTS.md`。
- 若需要新增 gdk 配合规则，应人工追加小节，再执行 `check-global-codex-health`。

## 2. 职责边界

| 层级 | 职责 | 更新方式 |
|---|---|---|
| `global-dev-kit/manifest.yaml` | Agent/Skill/Profile 单一事实源 | 修改后跑 `validate --strict` 与 `test` |
| `global-dev-kit/agents` | 角色 Agent 源资产 | 通过 gdk install 分发 |
| `global-dev-kit/skills` | 默认技能源资产 | 通过 gdk install 分发 |
| `global-dev-kit/optional-skills` | 按需技能源资产 | 用 `--with-optional-skill` 分发 |
| `~/.codex/agents` | 生产运行 Agent | 由 gdk install 写入 |
| `~/.codex/skills` | 生产运行 Skill | 由 gdk install 写入 |
| `~/.codex/AGENTS.md` | 全局代理行为规则 | 人工维护，不由 gdk 覆盖 |

## 3. 推荐安装组合

```bash
rtk bash -lc "cd global-dev-kit && bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile personal-core --extra-profile release-hardening --with-optional-skill planning-execution-loop --with-optional-skill skill-composition-governance --with-optional-skill security-supply-chain --with-optional-skill cross-team-handoff --with-optional-skill artifact-gated-lite --backup --install-report ../reports/gdk-install-report-$(date +%F).md --lock-version 0.3.0"
rtk scripts/check-global-codex-health.sh ~/.codex minimal
```

说明：

- `personal-core`：个人生产默认研发能力。
- `release-hardening`：发布、可靠性、安全强化。
- `planning-execution-loop`：长任务计划与恢复。
- `skill-composition-governance`：多技能组合治理。
- `security-supply-chain`：第三方资产引入审查。
- `cross-team-handoff`：团队交接。
- `artifact-gated-lite`：高风险变更轻量证据门禁。

## 4. `~/.codex/AGENTS.md` 建议追加小节

以下内容适合作为 `~/.codex/AGENTS.md` 的附加小节。不要替换个人原有规则。

```md
## global-dev-kit 配合规则

- `global-dev-kit` 是全局 Agent/Skill/Profile 的生产资产来源。
- gdk 只负责安装 `agents/` 与 `skills/`，不覆盖本文件。
- 不手工把参考仓资产直接复制进 `~/.codex/agents` 或 `~/.codex/skills`。
- gdk 资产更新必须先在 `llm_agent/global-dev-kit` 通过 `tests/run_all.sh`，再用 `scripts/devkit.sh install` 安装。
- 生产可用结论必须附 `llm_agent/scripts/check-gdk-harden-readiness.sh . --require-pilot` 证据。
- 涉及 `~/.codex` 运行目录时，必须附 `llm_agent/scripts/check-global-codex-health.sh ~/.codex minimal` 证据。

### gdk Skill 路由

- 长任务、跨会话恢复、复杂计划执行：优先 `planning-execution-loop`。
- 多技能触发冲突、profile 组合、fallback 判定：优先 `skill-composition-governance`。
- 第三方 skill、agent、脚本、参考资产引入前：必须使用 `security-supply-chain`。
- 跨团队交接、Owner 变更、签收复验：使用 `cross-team-handoff`。
- 高风险变更、共享契约、发布链路：叠加 `artifact-gated-lite`。
- 完成、提交、发布、可用性声明前：必须使用 `verification-before-completion`。
```

## 5. 不建议写入 `~/.codex/AGENTS.md` 的内容

- 参考仓全文分析。
- 一次性 pilot 报告。
- gdk 的完整 Agent/Skill 正文。
- 安装报告、备份路径历史列表。
- 需要频繁变化的 adoption matrix 明细。
- 任何密钥、账号、私有业务上下文。

这些内容应保留在 `llm_agent/reports`、`subrepos/adoption-matrix.md` 或 gdk 源文档中。

## 6. 更新流程

### 6.1 只更新 gdk 源资产

```bash
rtk bash -lc "cd global-dev-kit && bash scripts/devkit.sh test"
```

### 6.2 重新安装到 `~/.codex`

```bash
rtk bash -lc "cd global-dev-kit && bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile personal-core --extra-profile release-hardening --with-optional-skill planning-execution-loop --with-optional-skill skill-composition-governance --with-optional-skill security-supply-chain --with-optional-skill cross-team-handoff --with-optional-skill artifact-gated-lite --backup --install-report ../reports/gdk-install-report-$(date +%F).md --lock-version 0.3.0"
rtk scripts/check-global-codex-health.sh ~/.codex minimal
```

### 6.3 修改 `~/.codex/AGENTS.md`

修改后至少运行：

```bash
rtk scripts/check-global-codex-health.sh ~/.codex minimal
```

若修改影响 gdk 生产结论，继续运行：

```bash
rtk scripts/check-gdk-harden-readiness.sh . --require-pilot
```

## 7. 冲突处理

| 冲突 | 处理方式 |
|---|---|
| `~/.codex/AGENTS.md` 规则与 gdk skill 触发冲突 | 以 `~/.codex/AGENTS.md` 为运行时优先级，并回灌 gdk routing 文档 |
| 多个 skill 同时像主技能 | 使用 `skill-composition-governance` 判定 primary/supporting/fallback |
| optional skill 越来越多导致触发噪音 | 调整 profile 或减少默认安装 optional skill |
| 参考仓资产想直接进入生产 | 先走 `security-supply-chain` + adoption matrix + gdk 门禁 |
| 安装后行为异常 | 使用 install report 中的 backup 回滚，并记录报告 |

## 8. 验收标准

可以声明 `~/.codex/AGENTS.md` 与 gdk 配合健康，必须满足：

```bash
rtk scripts/check-global-codex-health.sh ~/.codex minimal
rtk scripts/check-runtime-routing.sh .
rtk scripts/check-gdk-harden-readiness.sh . --require-pilot
```

若任一命令失败，只能声明“已更新文档/配置，尚未生产放行”。
