# Agent Dev Kit

`agent-dev-kit`（adk）是通用 Agent/Skill/Profile/Workflow 资产包。它把参考资料、官方文档和工程经验压实为可验证、可回滚、可迭代的 ADK 资产；资产可以导出到显式声明的 tool target，但 core 不绑定任何单一运行时。

当前版本：`2.9.0`。

## 1. 定位边界

adk 的核心定位是“平台中立的 Agent 开发套件”。当前主力验证场景是嵌入式全栈开发，但嵌入式能力通过 `embedded-fullstack` profile 和领域技能承载，不把某个运行平台写成 core 前提。

adk 负责：

1. 维护 Agent、Skill、Profile、Workflow、Manifest 和治理契约的单一事实源。
2. 提供需求、设计、实现、验证、评审、发布和复盘的门禁资产。
3. 管理官方参考来源的 freshness、review status 和 promotion gate。
4. 通过显式 tool target 适配不同运行时。
5. 防止平台专属 handoff、用户目录写入和兼容残留混入 ADK core。

adk 不负责：

1. 替代具体运行时的全局策略文件、用户配置或企业策略。
2. 默认安装到任何平台的用户运行目录。
3. 在 core 中保留平台专属兼容链路。
4. 绕过验证、review、rollback 直接发布资产。

## 2. 领域覆盖

通用 ADK 能力覆盖：

- 需求收敛、任务拆解、接口契约、计划执行、代码审查和完成前验证。
- Profile 组合、Skill 触发、上下文分层、官方资料提升和运行时边界治理。
- 变更工件、Evidence Index、发布加固、回滚和复盘。
- 第三方参考吸收、MCP/plugin/hook/automation 的准入边界。

嵌入式全栈 profile 额外覆盖：

- SoC/MCU/MPU、板级约束、电源、时钟、复位、pinmux 和 memory map。
- BootROM、SPL、Bootloader、secure boot、分区、镜像、rootfs 和启动失败恢复。
- BSP、设备树、Kconfig、Linux kernel、RTOS、bare-metal、AMP/SMP、IPC、调度和内存。
- 驱动、寄存器、中断、DMA、协议栈、组件/中间件、网络/文件系统/升级/诊断。
- 设备侧应用、Linux 用户态工具、系统服务、CLI/daemon、配置和升级链路。
- 上位机、产测、诊断、烧录、标定、日志分析、HIL 控制和调试辅助工具。
- host unit、ctest、QEMU/SIL、HIL、静态分析、故障注入、长稳、OTA/回滚演练。
- 量产、RMA、现场日志、远程升级、设备健康检查和现场恢复流程。

## 3. 当前资产

| 类型 | 入口 |
|---|---|
| Manifest | `manifest.yaml` |
| Agents | `agents/<name>/AGENTS.md` |
| Core skills | `skills/<name>/SKILL.md` |
| Optional skills | `optional-skills/<name>/SKILL.md` |
| Workflows | `manifest.yaml:workflows` |
| Governance manifests | `manifests/*.json` |
| Runbooks | `docs/runbooks/` |
| Tests | `tests/run_all.sh` |

当前 tool targets 在 `manifest.yaml:tool_targets` 声明：

- `claude-code`
- `hermes-agent`
- `opencode`

新增 target 必须显式声明检测路径、agent/skill 输出目录、转换语义、拒绝条件和回滚路径，并通过 `runtime-boundary` 验证。

## 4. Profiles

| Profile | 推荐场景 |
|---|---|
| `core` | 通用 ADK 主干能力 |
| `personal-core` | 个人通用 ADK 核心配置 |
| `embedded-fullstack` | 嵌入式全栈开发配置 |
| `team-core` | 团队协作、交接和评审 |
| `release-hardening` | 发布前质量、验证和安全强化 |
| `openspec-driven` | Spec 驱动变更 |
| `large-refactor` | 大型重构 |
| `incident-response` | 事故响应 |
| `research-intake` | 参考资料吸收 |

## 5. 快速开始

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh install --tool claude-code --profile core --target /tmp/adk-target --mode copy
bash scripts/devkit.sh convert --target claude-code --profile core --out dist --clean
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh official-docs-governance --summary-json
bash scripts/devkit.sh test
```

常用入口：

- `docs/commands.md`：完整命令参考。
- `docs/usage.md`：常用工作流。
- `docs/adk-usage-guide.md`：面向使用者的 ADK 概念、profile、工作流、资产变更和提交门禁指南。
- `docs/runbooks/workspace-maintenance-guide.md`：维护与发布前检查。
- `docs/runbooks/mcp-governance.md`：MCP、plugin、automation 外部能力准入。
- `docs/reference/openai-developers-reference.md`：OpenAI 官方资料采纳记录，作为 provenance/reference，不作为 core 运行时绑定。

## 6. 质量门禁

最小门禁：

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh official-docs-governance --summary-json
bash tests/run_all.sh
```

变更分级：

| 变更范围 | 最小验证 |
|---|---|
| 文档说明 | `bash scripts/devkit.sh validate --strict` |
| Agent/Skill/Profile/Manifest | `bash scripts/devkit.sh validate --strict` + `bash tests/run_all.sh --fail-fast` |
| install/convert/runtime 脚本 | 相关单测 + `bash tests/run_all.sh` |
| MCP/plugin/hook/automation 契约 | `bash scripts/devkit.sh official-docs-governance --summary-json` + 相关契约测试 |
| 发布前放行 | `bash scripts/devkit.sh test` + rollback 说明 |

没有验证证据，不声明可发布、可合并或生产可用。

## 7. 参考吸收

adk 可以吸收 Claude Code、Codex、TRAE、OpenClaw、OpenAI Developers 或其他平台的优秀实践，但吸收时必须先做 practice-source 字段映射：

1. 区分“来源平台特性”和“可迁移 ADK 契约”。
2. 官方 URL、source id、产品名可保留为 citation metadata。
3. 被提升为 ADK rule、manifest、skill 或 runbook 时，必须转为平台中立表达。
4. 不能因为去绑定而删除可借鉴的平台名称；也不能因为引用平台教程而把 ADK core 绑定到该平台。

## 8. 运行时边界

ADK core 的硬边界：

- 不声明平台专属默认 target。
- 不提供平台专属 handoff 命令。
- 不默认写用户运行目录。
- 不把兼容迁移期脚本保留为 active path。
- 不把官方资料中的产品名提升为 core runtime 依赖。

`scripts/check-runtime-boundary.sh` 会阻止平台专属 target、脚本、测试和 active runtime 文档残留回流。例外只允许作为 reference、archive、source metadata 或 negative gate 出现。
