# Usage

## 1) 预检查

```bash
cd agent-dev-kit
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh validate --quick
bash scripts/devkit.sh test
bash scripts/devkit.sh file-modes
```

说明：

- `validate --strict`：检查 manifest、路径、frontmatter、profile 引用、workflow、context layer、skill 入口长度和质量分级。
- `validate --quick`：快速结构检查，适合编辑中间态。
- `test`：全量回归，包含 validate、格式、内容质量、文件权限、安装、profile coherence、optional、convert、workflow、catalog、trigger matrix。
- `file-modes`：按 Git index 检查 tracked 文件权限；`100644` 不可执行，`100755` 可执行，使用 `--fix` 可修复工作区权限漂移。

## 2) Profile 选择

| Profile | 推荐场景 |
|---|---|
| `core` | 通用研发最小主干 |
| `personal-core` | 个人 `~/codex -> ~/.codex` 生产推荐 |
| `embedded-fullstack` | 嵌入式全栈推荐 profile |
| `release-hardening` | 发布前强化 |
| `team-core` | 团队交付与交接 |
| `openspec-driven` | Spec 驱动变更 |
| `large-refactor` | 大型重构 |
| `incident-response` | 事故响应 |
| `research-intake` | 参考仓吸收 |

Profile 继承一致性检查：

```bash
bash scripts/check-profile-coherence.sh
```

## 3) 资产安装与生产交接

```bash
# 自动识别工具并软链接安装
bash scripts/devkit.sh install --tool auto --mode symlink --profile embedded-fullstack

# 本地临时目标目录安装 core + 强化 profile（仅用于非 Codex 工具测试 install 行为）
bash scripts/devkit.sh install --tool claude-code --target /tmp/adk-claude-target --mode copy --profile core --extra-profile release-hardening

# 生产推荐：导出符合 ~/codex 源资产与 manifest fragment 规范的 handoff
bash scripts/devkit.sh convert --target codex --profile personal-core --extra-profile release-hardening --with-optional-skill adk-planning-execution-loop --with-optional-skill adk-skill-composition-governance --with-optional-skill adk-security-supply-chain --with-optional-skill adk-cross-team-handoff --codex-profile team-collab --out ../reports/adk-codex-handoff --clean

# 在 /tmp 的 ~/codex 副本中合并 handoff，并运行 ~/codex build/doctor/check-skills
bash scripts/devkit.sh codex-handoff --codex-root ~/codex
```

参数说明：

- `--tool`：`auto|claude-code|hermes-agent|opencode`；Codex 生产链路使用 `convert --target codex`
- `--mode`：`symlink|copy`
- `--profile`：主 profile（默认 `core`）
- `--extra-profile`：可选叠加 profile（可重复）
- `--with-optional-skill`：按需叠加可选技能（可重复）
- `--codex-profile`：`target=codex` 时写入 `~/codex` manifest fragment 的 profile，默认 `team-collab`
- `--target`：覆盖 manifest 里的工具默认根目录
- `--backup`：安装前备份目标 `agents/skills`
- `--install-report`：生成安装报告
- `--lock-version`：要求 manifest version 匹配

生产安装纪律：

- 生产链路推荐先导出到交接目录，再由 `~/codex` 注册、build、doctor、apply 到 `~/.codex`。
- `target=codex` 的导出物必须包含 `src/codex-home/vendor/...` 与 `manifest-fragments/*.json`，其中至少包含 agents、skills、workflows、mcp_servers、change_sets 五类 fragment，不能是 `~/.codex` 运行目录形态。
- adk 不直接写入 `~/.codex`，避免绕过 `~/codex` 的 manifest、drift 和 rollback 管理。
- apply 后运行 `llm_agent/scripts/check-global-codex-health.sh ~/.codex minimal`。（注意: 此脚本在 llm_agent 父仓库中，非本仓库）
- 若用于生产放行，还需运行 `llm_agent/scripts/check-adk-harden-readiness.sh . --require-pilot`。（注意: 此脚本在 llm_agent 父仓库中，非本仓库）

## 4) 资产转换

```bash
# 导出到 Claude Code
bash scripts/devkit.sh convert --target claude-code --profile embedded-fullstack --out dist --clean

# 导出到 Hermes Agent（叠加发布强化）
bash scripts/devkit.sh convert --target hermes-agent --profile core --extra-profile release-hardening --out dist --clean

# 导出 Codex handoff，并包含可选技能
bash scripts/devkit.sh convert --target codex --profile core --with-optional-skill adk-test-flakiness-triage --codex-profile team-collab --out dist --clean
```

## 5) 目录索引与触发匹配

```bash
# 生成 Agent/Skill/Profile 索引
bash scripts/devkit.sh catalog build

# 关键词检索
bash scripts/devkit.sh catalog find --type optional-skill --keyword 事故

# 触发匹配（0 命中，1 未命中）
bash scripts/devkit.sh match --skill adk-requirements-triage --text "收到模糊需求或跨团队需求时"
bash scripts/devkit.sh match --skill adk-planning-execution-loop --scope optional-skill --text "复杂任务需要计划审查和执行检查点时"
```

技能组合规则：

- 一个场景只有一个 primary skill。
- supporting skills 只补检查项，不抢入口。
- 多技能冲突时使用 `adk-skill-composition-governance`。
- 第三方资产进入全局环境前使用 `adk-security-supply-chain`。

## 6) 工作流命令

```bash
# 创建变更提案
bash scripts/devkit.sh propose --change can-fd-bringup --title "新增 CAN-FD bring-up"

# 标记已实施
bash scripts/devkit.sh apply --change can-fd-bringup

# 触发验证并生成 verify-report.md
bash scripts/devkit.sh verify --change can-fd-bringup

# 评审分级并生成 review-report.md
bash scripts/devkit.sh review --change can-fd-bringup --result pass --blockers 0 --majors 0 --minors 1

# 归档到 docs/changes/archive
bash scripts/devkit.sh archive --change can-fd-bringup
```

命令级 Evidence Index：

```bash
bash scripts/devkit.sh evidence append --file docs/changes/can-fd-bringup/negative-results.md --command "bash tests/run_all.sh" --exit-code 0 --summary "all tests passed" --evidence-path docs/changes/can-fd-bringup/verify-report.md --layer Workflow --artifact verify-report
```

注意事项：
- 必须按 `propose -> apply -> verify -> review -> archive` 顺序执行。
- `review` 只接受 `verified` 状态，`archive` 默认只接受 `review-passed` 状态。
- `proposal.md` 需补全单问题、充分性、边界、重复性与 breaking change 检查项。

## 7) 测试与回归

```bash
# 全量测试（validate + format + install + profile coherence + optional + convert + workflow + catalog + trigger matrix）
bash scripts/devkit.sh test

# 单项检查
bash scripts/check_format.sh
bash scripts/validate-assets.sh --strict
bash scripts/check-profile-coherence.sh
```

## 8) `~/codex` 与 `~/.codex/AGENTS.md` 配合

adk 不覆盖 `~/codex` 或 `~/.codex/AGENTS.md`。推荐分工：

- `~/codex/src/codex-home` 与 `~/codex/manifests`：Codex Home 源资产、profile、skill、agent、workflow 声明。
- `~/.codex/AGENTS.md`：全局策略、命令硬约束、流程升级/降级、技能路由原则。
- `~/.codex/agents`：由 `~/codex` apply 后的 Agent。
- `~/.codex/skills`：由 `~/codex` apply 后的 Skills、系统保留 skill 与已治理个人技能。
- `agent-dev-kit`：源资产、测试、profile、runbook、导出物。

详细说明见：

```text
docs/codex-agents-integration.md
```

## 9) 生产验证与回滚

生产验证由 `llm_agent` 根脚本统一执行：

```bash
rtk ../scripts/check-adk-harden-readiness.sh . --require-pilot
```

若 apply 后异常：

1. 从 `~/codex/build/apply-plan*.json` 或 backup 找到回滚依据。
2. 经用户确认后运行 `~/codex/scripts/rollback.sh` 或恢复备份。
3. 运行 `rtk ../scripts/check-global-codex-health.sh ~/.codex minimal`。
4. 在 `reports/` 写入回滚记录。
