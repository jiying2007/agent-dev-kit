# Agent Dev Kit

`agent-dev-kit`（adk）是通用 Agent/Skill/Profile/Workflow 资产包。它把参考资料、官方文档和工程经验压实为可验证、可回滚、可迭代的 ADK 资产；资产可以导出到显式声明的 tool target，但 core 不绑定任何单一运行时。

当前版本：`5.1.0`（本地候选；尚未 tag、发布或刷新到 live）。

发布支持基线为 Python 3.11+，运行依赖固定为 `PyYAML==6.0.3` 与 `jsonschema==4.26.0`。PyYAML 用于仍以 YAML 表达的 workflow/target 等独立合同，不再用于 Manifest 镜像。Python 3.8/3.9 已退出本项目支持范围；源码在旧解释器上偶然可运行不构成发布兼容承诺。

当前组件发布状态是 **5.1.0 release-train candidate**。产品级成熟度与 ADK 组件发布成熟度分离管理；运行时一致性按 `static / smoke / native / certified` 独立记录。ADK 不再把产品 M3/M5 用作组件版本状态，也不会因为 direct target 仍为 experimental 就伪造 runtime-certified。

`scripts/devkit.sh` 未设置 override 时按 `python3.12 -> python3.11 -> python3`
确定性选择解释器；可用 `ADK_PYTHON_BIN` 显式覆盖。发布和认证验证应设置
`ADK_REQUIRE_SUPPORTED_PYTHON=1`，或使用受控 Docker local-CI parity；旧 Python
只允许运行 `doctor` 或产生明确标记的开发期结果，不能升级为发布证据。

## 1. 定位边界

adk 的核心定位是“平台中立的 Agent 资产编译与交付控制面”。当前主力验证场景是嵌入式全栈开发，但嵌入式能力通过 `embedded-fullstack` profile 和领域技能承载，不把某个运行平台写成 core 前提。ADK 不实现 LLM 推理循环、session scheduler 或生产 Agent runtime。

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
| Manifest SSOT | `manifest.json` + `manifests/manifest.schema.json` |
| Agents | `agents/<name>/AGENTS.md` |
| Core skills | `skills/<name>/SKILL.md` |
| Optional skills | `optional-skills/<name>/SKILL.md` |
| Workflows | `manifest.json:workflows` |
| Governance manifests | `manifests/*.json` |
| Runbooks | `docs/runbooks/` |
| Tests | `tests/run_all.sh` |

`manifest.json` 是唯一结构化 Manifest；不维护 YAML 镜像或其它平行 SSOT。需要人类可读视图时由 catalog/docs 从 canonical JSON 生成。

当前 direct tool targets 在 `manifest.json:tool_targets` 声明：

- `claude-code`（`experimental`）
- `hermes-agent`（`experimental`，仅支持 Skill）
- `opencode`（`experimental`）

三个 target 已通过原生路径、frontmatter、权限、support tree、export/install 同源 hash 和 caller-supplied fixture smoke；尚未取得真实目标运行时的 discovery/load/trigger 证据，因此不得提升为 stable 或 runtime-certified。新增 target 必须提供 versioned target contract、检测路径、agent/skill 输出目录、转换语义、拒绝条件和回滚路径，并通过 `target check`、`runtime-boundary` 与真实 runtime smoke。

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
bash scripts/devkit.sh target check --all --level static --summary-json
bash scripts/devkit.sh doctor --require-runtime codex --require-runtime claude --summary-json
bash scripts/devkit.sh export --target claude-code --profile core --out dist --clean
bash scripts/devkit.sh install plan --tool claude-code --profile core --target /tmp/adk-target --mode copy --output /tmp/adk-plan.json
bash scripts/devkit.sh install apply --plan /tmp/adk-plan.json
bash scripts/devkit.sh benchmark run --iterations 5 --summary-json
bash scripts/devkit.sh security check --summary-json
bash scripts/devkit.sh eval run --suite deterministic --summary-json
bash scripts/devkit.sh eval effect --contract manifests/effect_eval_contract.json --summary-json
bash scripts/devkit.sh eval campaign plan --contract manifests/software_m5_eval_contract_v5.json --summary-json
bash scripts/devkit.sh eval repository plan --contract manifests/repository_runtime_eval_contract.json --summary-json
bash scripts/devkit.sh eval repository certify --contract manifests/repository_runtime_eval_contract.json --report <repository-report.json> --summary-json
bash scripts/devkit.sh release check --summary-json
bash scripts/devkit.sh release runtime-build --profile team-core --out dist --summary-json
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh official-docs-governance --summary-json
bash scripts/devkit.sh harness readiness --root . --summary-json
bash scripts/devkit.sh test
```

`eval repository certify` 对默认 clean-room contract 只返回 `fixture-pass`，不会被 Software M5 当作真实 repository campaign；真实 `pass` 还要求 owner-approved task 与已审查、digest-pinned 的 available adapter。

常用入口：

- `docs/commands.md`：完整命令参考。
- `docs/usage.md`：常用工作流。
- `docs/adk-usage-guide.md`：面向使用者的 ADK 概念、profile、工作流、资产变更和提交门禁指南。
- `docs/runbooks/workspace-maintenance-guide.md`：维护与发布前检查。
- `docs/runbooks/codex-team-runtime-distribution.md`：私有 ADK Release 到团队 Codex 的精简分发链。
- `docs/runbooks/mcp-governance.md`：MCP、plugin、automation 外部能力准入。
- `docs/reference/openai-developers-reference.md`：OpenAI 官方资料采纳记录，作为 provenance/reference，不作为 core 运行时绑定。

Python core 可以构建为 wheel 供集成测试或二次开发使用；资产本体仍由独立 ADK checkout/release bundle 管理。使用已安装的 `adk` console script 执行资产命令时，应在 checkout 内运行或设置 `ADK_ROOT=/path/to/agent-dev-kit`，找不到资产根目录会明确失败。仅依赖外部工件的 `install rollback`、`eval compare` 和 `release publish` 不要求 checkout，可从非仓库 cwd 执行。

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
| install/export/release 脚本 | `bash tests/test_product_maturity_v5.sh` + `bash tests/test_software_m5_ready.sh` + `bash tests/run_all.sh` |
| MCP/plugin/hook/automation 契约 | `bash scripts/devkit.sh official-docs-governance --summary-json` + 相关契约测试 |
| 发布前放行 | `bash scripts/devkit.sh security check` + `bash scripts/devkit.sh release check` + 本地 release rehearsal + `bash scripts/devkit.sh test` + rollback 说明 |

没有验证证据，不声明可发布、可合并或生产可用。

本地执行与 CI 相同的 Python 质量门禁：

```bash
python -m pip install '.[quality]'
ruff check src tools tests/fixtures/fake_target_runtime.py
pip-audit --strict --progress-spinner off .
```

工具未安装或审计数据不可取得时必须报告 unavailable/blocked，不能把未执行记为通过。

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
