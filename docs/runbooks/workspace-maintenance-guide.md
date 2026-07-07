# Workspace Maintenance Guide

This runbook keeps ADK assets generic, validated and reviewable. It applies to `agent-dev-kit` itself, not to any runtime user's global configuration.

## 1. 定位

`agent-dev-kit` 负责维护通用 ADK 源资产：

1. Agent、Skill、Profile、Workflow 和 Manifest。
2. 需求、设计、实现、验证、评审、发布、复盘门禁。
3. 官方参考资料与第三方参考资料的吸收、映射和提升。
4. tool target 的显式适配契约。
5. runtime-boundary、freshness、回滚和测试证据。

adk 不直接替代具体运行时的全局策略文件，也不默认写任何用户运行目录。任何 target 适配都必须是显式、可审查、可禁用、可回滚的。

## 2. 目录职责

| 路径 | 职责 | 维护要求 |
|---|---|---|
| `AGENTS.md` | 本仓协作规则和安全边界 | 规则变化后跑相关门禁 |
| `manifest.yaml` | Agent/Skill/Profile/tool target/workflow 单一事实源 | 修改后跑 strict validate 和 profile/workflow 检查 |
| `agents/` | 角色 Agent 定义 | 保持职责单一，不写平台专属安装路径 |
| `skills/` | core skills | 入口短读，长证据放 references 或 docs |
| `optional-skills/` | 可选 skills | 默认不进入 core profile |
| `manifests/` | 治理契约和官方资料提升产物 | schema、source、review 状态必须可追溯 |
| `scripts/` | 统一入口和门禁脚本 | 新脚本必须有 smoke 或定向测试 |
| `docs/` | 命令说明、runbook、参考资料、变更工件 | 文档必须与脚本入口一致 |
| `tests/` | 回归、smoke 和治理测试 | 共享行为变化必须补测试 |

## 3. 日常维护循环

1. 明确本次变更范围、非目标和验收命令。
2. 修改 `manifest.yaml`、agents、skills、docs 或 scripts。
3. 先跑定向检查。
4. 再跑共享门禁。
5. 记录验证证据、风险和回滚方式。

常用命令：

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh official-docs-governance --summary-json
bash scripts/devkit.sh workflow-closure --profile core
bash scripts/devkit.sh goal check --summary-json
bash scripts/devkit.sh capability health --summary-json
bash scripts/devkit.sh perf budget --summary-json
bash tests/run_all.sh --fail-fast
```

## 4. 变更分级

| 变更类型 | 最小验证 | 说明 |
|---|---|---|
| README、usage、commands、runbook | `bash scripts/devkit.sh validate --strict` + 相关文档测试 | 防止文档与 CLI 漂移 |
| Agent/Skill 内容 | `bash scripts/devkit.sh validate --strict` + `bash tests/run_all.sh --fail-fast` | 覆盖 frontmatter、触发和质量规则 |
| Profile/manifest | `bash scripts/devkit.sh validate --strict` + `bash scripts/devkit.sh workflow-closure --profile core` | 防止未知引用和 profile 闭包漂移 |
| 目标/功能/性能契约 | `bash scripts/devkit.sh goal check --summary-json` + `bash scripts/devkit.sh capability health --summary-json` + `bash scripts/devkit.sh perf budget --summary-json` | 防止目标、能力和预算只停留在文档声明 |
| install/convert/runtime 脚本 | 相关单测 + `bash tests/run_all.sh` | 防止交付路径回归 |
| MCP/plugin/hook/automation 契约 | `bash scripts/devkit.sh official-docs-governance --summary-json` + 安全审查 | 默认 report-only |
| 发布前 | `bash scripts/devkit.sh test` | 必须带 rollback note |

## 5. Runtime Boundary

硬边界：

- core 不声明平台专属默认 target。
- active docs 不提供平台专属 handoff 作为默认路径。
- active scripts 不默认写用户运行目录。
- 已下线兼容脚本不得作为 active path 回流。
- 官方资料中的产品名只能作为 citation metadata 或 reference context；提升为 ADK 契约时必须平台中立。

检查命令：

```bash
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh runtime-boundary --summary-json
```

如果确需新增 target：

1. 在 `manifest.yaml:tool_targets` 声明 target。
2. 补齐 install/convert 语义、默认根目录、agents/skills 输出目录和 detect 规则。
3. 补充安全边界、dry-run、禁用路径和回滚路径。
4. 更新 `docs/commands.md` 与 `docs/usage.md`。
5. 增加定向测试后跑全量回归。

## 6. 参考资料吸收

吸收外部平台、官方文档或开源仓库时，按以下顺序：

1. 记录 source、retrieved_at、review_status、expires_at。
2. 区分 source metadata、平台专属行为和可迁移 ADK contract。
3. 先进入 reference 或 adoption matrix。
4. 通过 review 后再提升到 manifest、skill、agent 或 runbook。
5. 提升后跑 freshness、runtime-boundary 和相关回归。

平台名称不需要为了“去绑定”而机械删除；但平台专属命令、目录和 handoff 不得进入 ADK core 默认路径。

## 7. MCP、Plugin 与 Automation

外部能力默认高风险，必须先满足 `docs/runbooks/mcp-governance.md`：

- 只读优先，写操作单独审批。
- 默认 report-only，不自动发送、发布、删除或覆盖。
- 凭证来自运行环境或密钥管理器，不写入 docs、skill、manifest 或日志。
- 每个工具必须声明 owner、权限边界、deny-path、smoke 证据和禁用方式。

## 8. 回滚

回滚前先确认：

1. 受影响文件、target 和 profile。
2. 是否存在转换输出、安装报告、release note 或备份。
3. 是否需要用户确认覆盖目标目录。
4. 回滚后运行哪些验证命令。

不得使用破坏性命令绕过 Git 审计。涉及目标运行目录或生产配置时，先 dry-run，再执行，再验证。

## 9. 完成标准

一次维护任务完成前至少要有：

- 变更摘要。
- 验证命令和结果。
- runtime-boundary 结论。
- 若涉及 `perf`、`ops` 或测试运行器，附 summary-json、report-only 或 timing 证据。
- 若涉及官方资料，附 freshness/governance 结论。
- 若涉及外部能力，附安全边界和回滚方式。
- 剩余风险或未处理项。
