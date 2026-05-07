# Global Dev Kit

`agent-dev-kit`（gdk）是面向 `~/.codex` 等开发代理运行目录的 Agent/Skill/Profile 生产资产包。它的目标是把参考仓中的优秀方法论压实为可安装、可验证、可回滚、可持续迭代的工程资产。

当前版本：`2.6.0`。

## 1. 核心定位

gdk 不是参考仓集合，也不是直接替换 `~/.codex/AGENTS.md` 的全局策略文件。它负责：

1. 维护 Agent/Skill/Profile 单一事实源：`manifest.yaml`。
2. 提供安装、转换、匹配、catalog、workflow、evidence 命令。
3. 用测试和门禁压实 Agent/Skill/Workflow/runbook。
4. 把稳定资产安装到 `~/.codex/agents` 与 `~/.codex/skills`。
5. 为真实生产使用提供安装报告、备份、pilot 与健康检查证据。

## 2. 当前资产概览

- Agents：10 个角色 Agent。
- Core Skills：28 个稳定技能。
- Optional Skills：10 个可选技能。
- Profiles：`core`、`personal-core`、`embedded-fullstack`、`release-hardening`、`adk-artifact-gated-lite`、`team-core`、`openspec-driven`、`large-refactor`、`incident-response`、`research-intake`。
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
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh validate --strict"
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh test"
```

若已在 `agent-dev-kit` 目录内，普通环境可直接执行：

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh test
```

## 5. 生产安装到 `~/.codex`

推荐安装组合：

- 主 profile：`personal-core`
- 叠加 profile：`release-hardening`
- optional skills：`adk-planning-execution-loop`、`adk-skill-composition-governance`、`adk-security-supply-chain`、`adk-cross-team-handoff`、`adk-artifact-gated-lite`

命令：

```bash
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile personal-core --extra-profile release-hardening --with-optional-skill adk-planning-execution-loop --with-optional-skill adk-skill-composition-governance --with-optional-skill adk-security-supply-chain --with-optional-skill adk-cross-team-handoff --with-optional-skill adk-artifact-gated-lite --backup --install-report ../reports/gdk-install-report-$(date +%F).md --lock-version 2.0.0"
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
| `adk-artifact-gated-lite` | 高风险变更 | 复用 `core`，配合 optional skill 产出轻量 artifact 门禁 |
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
| `adk-test-flakiness-triage` | 测试波动定位 |
| `adk-cross-team-handoff` | 跨团队交接 |
| `adk-incident-rca-report` | 事故复盘 |
| `adk-artifact-gated-lite` | 高风险 artifact 门禁 |
| `adk-planning-execution-loop` | 长任务计划、检查点、恢复和收口 |
| `adk-skill-composition-governance` | 主技能、辅助技能、fallback、弃用治理 |
| `adk-security-supply-chain` | 第三方资产、脚本、技能引入前审查 |

安装 optional skill 示例：

```bash
bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile personal-core --with-optional-skill adk-planning-execution-loop
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

## 版本 2.0.0 新增功能

### 文档体系完善
- **快速入门指南** (`docs/quick-start.md`): 帮助新用户快速上手
- **故障排除指南** (`docs/troubleshooting.md`): 解决常见问题
- **最佳实践指南** (`docs/best-practices.md`): 使用最佳实践
- **贡献指南** (`docs/CONTRIBUTING.md`): 如何为项目做贡献

### 生产部署能力
- **安装备份和回滚** (`scripts/backup-rollback.sh`): 完整的备份恢复机制
- **健康检查** (`scripts/health-check.sh`): 全面的系统健康检查
- **版本管理** (`scripts/version-manager.sh`): 版本锁定和升级路径

### 运行手册
- **生产部署运行手册** (`docs/runbooks/production-deployment.md`): 完整的部署指南

### 质量保证
- 所有测试通过 (59/59)
- 健康检查全部通过
- 质量门禁全部通过
- 版本已锁定为 2.0.0

## 使用新功能

### 健康检查
```bash
# 执行所有健康检查
bash scripts/health-check.sh check-all

# 详细输出
bash scripts/health-check.sh check-all --verbose
```

### 安装备份
```bash
# 创建备份
bash scripts/backup-rollback.sh backup --target ~/.codex

# 列出备份
bash scripts/backup-rollback.sh list --target ~/.codex

# 恢复备份
bash scripts/backup-rollback.sh restore --target ~/.codex --version 20260505
```

### 版本管理
```bash
# 查看当前版本
bash scripts/version-manager.sh current

# 锁定版本
bash scripts/version-manager.sh lock --version 2.0.0

# 升级版本
bash scripts/version-manager.sh upgrade --target 1.1.0
```


## 完整功能列表

### 文档体系
- **快速入门指南** (`docs/quick-start.md`): 帮助新用户快速上手
- **使用指南** (`docs/usage.md`): 详细的使用说明
- **命令参考** (`docs/commands.md`): 所有命令的详细说明
- **故障排除指南** (`docs/troubleshooting.md`): 解决常见问题
- **最佳实践指南** (`docs/best-practices.md`): 使用最佳实践
- **贡献指南** (`docs/CONTRIBUTING.md`): 如何为项目做贡献

### 生产部署能力
- **安装备份和回滚** (`scripts/backup-rollback.sh`): 完整的备份恢复机制
- **健康检查** (`scripts/health-check.sh`): 全面的系统健康检查
- **版本管理** (`scripts/version-manager.sh`): 版本锁定和升级路径

### 运行手册
- **生产部署运行手册** (`docs/runbooks/production-deployment.md`): 完整的部署指南
- **兼容性矩阵** (`docs/runbooks/compatibility-matrix.md`): 兼容性说明
- **团队交付** (`docs/runbooks/team-delivery.md`): 团队协作指南
- **上游集成** (`docs/runbooks/upstream-intake.md`): 上游集成指南

### 质量保证
- 所有测试通过 (59/59)
- 健康检查全部通过
- 质量门禁全部通过
- 版本已锁定为 2.0.0

## 使用新功能

### 健康检查
```bash
# 执行所有健康检查
bash scripts/health-check.sh check-all

# 详细输出
bash scripts/health-check.sh check-all --verbose

# 检查特定项目
bash scripts/health-check.sh check-structure
bash scripts/health-check.sh check-dependencies
bash scripts/health-check.sh check-configuration
bash scripts/health-check.sh check-tests
bash scripts/health-check.sh check-quality
```

### 安装备份
```bash
# 创建备份
bash scripts/backup-rollback.sh backup --target ~/.codex

# 列出备份
bash scripts/backup-rollback.sh list --target ~/.codex

# 恢复备份
bash scripts/backup-rollback.sh restore --target ~/.codex --version 20260505

# 验证备份
bash scripts/backup-rollback.sh verify --version 20260505

# 回滚版本
bash scripts/backup-rollback.sh rollback --target ~/.codex --version 20260505
```

### 版本管理
```bash
# 查看当前版本
bash scripts/version-manager.sh current

# 锁定版本
bash scripts/version-manager.sh lock --version 2.0.0

# 解锁版本
bash scripts/version-manager.sh unlock

# 升级版本
bash scripts/version-manager.sh upgrade --target 1.1.0

# 比较版本
bash scripts/version-manager.sh compare --version 2.0.0 --target 1.1.0

# 生成变更日志
bash scripts/version-manager.sh changelog
```

## 完全体特性

### 1. 架构完善
- ✅ 标准化目录结构
- ✅ 完善的产物体系
- ✅ 完整的文档体系
- ✅ 增强的测试覆盖

### 2. 质量保证
- ✅ 完善的质量门禁体系
- ✅ 59个测试用例
- ✅ 完整的健康检查
- ✅ 版本锁定和升级路径

### 3. 文档体系
- ✅ 快速入门指南
- ✅ 使用指南
- ✅ 命令参考
- ✅ 故障排除指南
- ✅ 最佳实践指南
- ✅ 贡献指南

### 4. 生产部署
- ✅ 安装备份和回滚
- ✅ 健康检查和监控
- ✅ 版本管理
- ✅ 生产部署运行手册


## 版本 2.0.0 第四阶段新增功能

### 版本发布管理
- **版本发布管理脚本** (`scripts/release-manager.sh`): 完整的版本发布管理

### 监控和告警
- **监控和告警脚本** (`scripts/monitoring.sh`): 系统监控和告警机制

### 自动化运维
- **自动化运维脚本** (`scripts/auto-ops.sh`): 自动化运维脚本

### 性能优化
- **性能优化脚本** (`scripts/performance.sh`): 性能分析和优化

### 安全加固
- **安全加固脚本** (`scripts/security.sh`): 安全扫描和加固

## 使用新功能

### 版本发布管理
```bash
# 准备发布
bash scripts/release-manager.sh prepare --version 2.0.0

# 验证发布
bash scripts/release-manager.sh validate --version 2.0.0

# 构建发布包
bash scripts/release-manager.sh build --version 2.0.0

# 发布版本
bash scripts/release-manager.sh publish --version 2.0.0 --target production

# 回滚发布
bash scripts/release-manager.sh rollback --version 2.0.0 --target production

# 查看状态
bash scripts/release-manager.sh status
```

### 监控和告警
```bash
# 启动监控
bash scripts/monitoring.sh start --interval 60

# 停止监控
bash scripts/monitoring.sh stop

# 查看状态
bash scripts/monitoring.sh status

# 执行检查
bash scripts/monitoring.sh check

# 发送告警
bash scripts/monitoring.sh alert --email admin@example.com

# 生成报告
bash scripts/monitoring.sh report
```

### 自动化运维
```bash
# 每日运维
bash scripts/auto-ops.sh daily

# 每周运维
bash scripts/auto-ops.sh weekly

# 每月运维
bash scripts/auto-ops.sh monthly

# 清理临时文件
bash scripts/auto-ops.sh cleanup

# 优化性能
bash scripts/auto-ops.sh optimize

# 安全检查
bash scripts/auto-ops.sh security
```

### 性能优化
```bash
# 分析性能
bash scripts/performance.sh analyze

# 优化性能
bash scripts/performance.sh optimize --level basic

# 性能测试
bash scripts/performance.sh benchmark

# 生成报告
bash scripts/performance.sh report
```

### 安全加固
```bash
# 安全扫描
bash scripts/security.sh scan

# 安全加固
bash scripts/security.sh harden --level basic

# 安全审计
bash scripts/security.sh audit

# 生成报告
bash scripts/security.sh report
```

