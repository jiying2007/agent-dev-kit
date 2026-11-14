# Agent Dev Kit

`agent-dev-kit`（ADK）是平台中立的 Agent 资产契约、编译、验证、评测与分发 SDK。它把 Agent、Skill、Profile、Workflow、治理契约和证据模型压实为可验证、可回滚、可发布的资产；ADK core 不绑定单一模型提供商、IDE、CLI 或生产 Agent runtime。

## 权威状态模型

ADK 不再在 README 中维护“候选 / 已发布 / live”之类可漂移的手写状态副本。状态分为四个正交维度：

- **Source identity**：以 `manifest.json`、`.version-lock`、Git commit/tree 为权威。
- **Component release**：以不可变 tag、GitHub Release、release contract 和 artifact digest 为权威。
- **Runtime conformance**：以 target/runtime receipt 与证据级别 `static / smoke / native / certified` 为权威。
- **Product qualification**：由消费方/产品仓的 qualification 与 field evidence 独立决定，不由 ADK 组件版本继承。

`manifest.json` 当前 source version 为 `11.2.17`。受保护 `main` 的每个合并变更必须先前移 SemVer；successful-main CI 会自动执行 exact-SHA tag promotion 和 GitHub Release，因此健康主线在 promotion 完成后应与 latest immutable release 对齐。CI/promotion 执行窗口内允许短暂差异，持续的 **current main != latest immutable release** 必须视为 release blocker。

8.0.0 维护 CLI 迁移：`performance.sh optimize`、`auto-ops.sh cleanup/optimize` 仅输出有界只读计划，JSON 使用 `adk-maintenance-plan/v1` 与 `status=planned`；维护 `--apply` 返回 blocked、exit 2，不再自动删除文件或修改权限。调用方必须移除维护 `--apply` 并按 `applied=false` 处理报告；见 [维护迁移说明](docs/changes/20261006-comprehensive-contracts/design.md)。

ADK **源码管理、构建与发布控制面**仅支持 CPython **3.12.x**（`>=3.12,<3.13`），建议使用独立 `.venv` 和固定依赖 `PyYAML==6.0.3`、`jsonschema==4.26.0`；3.11 与未验证的 3.13+ 均不受支持。纯 Skill 消费端不需要 ADK Python。

**已部署的纯 Agent/Skill 资产不需要 ADK Python 环境。** 团队 Runtime Bundle 不包含 ADK 源码、Python 管理器、依赖和内部测试；运行时只需目标产品/CLI 能读取标准 Skill 文件。若某个独立 Skill 自身声明执行脚本或外部工具，其依赖由对应 Skill/目标 Runtime 单独声明，不得归因于 ADK 的 Python 构建基线。

| 位置 | Python 要求 | 权威证据 |
| --- | --- | --- |
| ADK 源码维护、安装管理 CLI、评测、打包与发布 | Python 3.12 `.venv` | 单套 Python 3.12 合同和全量回归 |
| GitHub Actions / 本地 Docker 构建 | Python 3.12 | 精确 SHA 的原生检查 |
| 已导出的纯 Codex/Claude/OpenCode Skills | **不要求 ADK Python** | Runtime Bundle 无 ADK Python/源码；实际消费仍需 runtime-native discovery/load/trigger 验证 |
| 独立依赖 Python 的特定 Skill | 由 Skill 自己声明 | 逐 Skill 的受控工具与运行时证据 |

提高源码最低版本是 **9.0.0** 的破坏性变更，不会改变原有 Skill 数据格式、隐式授权、已发布不可变版本或下游产品资格。

## 1. 定位边界

ADK 的核心定位是“Agent Asset Contract Kernel & SDK”。当前主力验证场景是嵌入式全栈开发，但领域能力通过 profile/skill 承载，不把某个平台写成 core 前提。

ADK 负责：

1. 维护 Agent、Skill、Profile、Workflow、Manifest 和治理契约的单一事实源。
2. 提供需求、设计、实现、验证、评审、发布和复盘的可执行门禁资产。
3. 提供 evidence、evaluation、distribution、target adapter 等稳定内核能力。
4. 通过 versioned adapter/target contract 适配不同工具和协议。
5. 防止平台专属 handoff、用户目录写入和兼容残留混入 core。

ADK 不负责：

1. LLM 推理循环、session scheduler 或生产 Agent runtime。
2. 替代具体运行时的全局策略、用户配置或企业策略。
3. 默认写入任何 live 用户目录。
4. 绕过验证、review、rollback 直接发布或升级资格状态。

## 2. 结构与 SSOT

| 能力 | 权威入口 |
|---|---|
| Manifest / asset catalog | `manifest.json` + `manifests/manifest.schema.json` |
| Agents | `agents/<name>/AGENTS.md` |
| Core skills | `skills/<name>/SKILL.md` |
| Optional skills | `optional-skills/<name>/SKILL.md` |
| Contracts / schemas | `contracts/`, `schemas/`, `manifests/*.json` |
| Evidence | `src/agent_dev_kit/evidence/` |
| Distribution / release | `src/agent_dev_kit/distribution/` |
| Target adapters | `src/agent_dev_kit/target_adapters/` |
| Execution policy | `src/agent_dev_kit/execution_policy/` |
| Tests | `tests/run_all.sh` |

`manifest.json` 是资产 composition root；不维护 YAML Manifest 镜像。需要人类可读视图时，由 catalog/docs 从 canonical 数据生成。

### Execution policy 命名迁移

`agent_dev_kit.execution_policy` 是唯一公共执行策略命名空间，准确表达“ADK 提供执行策略/门禁决策，但不是 runtime”。6.0 起不再提供 `agent_dev_kit.runtime_control` Python 兼容别名；协议 schema 中已有的 `runtime_control.*` identity 保持版本化、不可静默改写。

## 3. Runtime / protocol adapter 边界

Direct tool targets 由 `manifest.json:tool_targets` 声明。Codex 走外部 source-to-live handoff，不作为 ADK direct target。

MCP、A2A、OpenTelemetry GenAI 等外部标准只能通过 versioned adapter boundary 接入：

- 外部协议版本不得成为 ADK core 的隐式版本号。
- 协议升级必须有显式 adapter contract、兼容性证据与回滚边界。
- adapter/runtime receipt 不得提升产品 qualification。
- 没有真实 discovery/load/trigger 或 native receipt 时，不得声明 runtime-certified。Runtime receipt 的 production trust 由 `manifests/native_conformance_trust_registry.json` 管理；registry 默认无启用 authority，只有 target policy、authority/target scope、receipt/bundle digest、签名 identity/issuer 与固定 verifier binary 全部匹配时，production loader 才接受 runtime conformance。

详见 `docs/architecture/interoperability-boundaries.md`。

### 头脑风暴与设计拷问

`adk-structured-requirements-questioning` 作为只读 primary，提供 Explore / Challenge 多轮交互，支持 brainstorming、Grill Me、决策依赖和反例分析。已确认结果再交 `adk-requirements-triage`，明确实现任务不重启访谈。静态通过不代表多轮效果，评估协议见 `docs/evals/interactive-discovery-evaluation.md`。

## 4. Profiles

核心 profile 包括：`core`、`personal-core`、`embedded-fullstack`、`team-core`、`release-hardening`、`large-refactor`、`incident-response`、`research-intake`。

嵌入式 profile 覆盖 SoC/MCU/RTOS/Linux、Boot/BSP/驱动、协议栈、设备应用、产测/HIL、OTA/回滚、量产/RMA/现场恢复等工程链路。

## 5. 快速开始

先按任务选择主入口，结果中的 source、component release、runtime 与 product 状态分别判断：

| 我要做什么 | 主入口 | 后续路径与结果解释 |
| --- | --- | --- |
| 使用资产 | `bash scripts/devkit.sh doctor --summary-json` | 检查环境后选择 profile，按 [安装命令](docs/commands.md#install) 生成并审查 plan，再 apply、保留 receipt；取消后按恢复说明核对 staging/backup。Codex 使用外部 source-to-live 交接链。 |
| 判断当前是否可用 | `bash scripts/devkit.sh target check --all --level static --summary-json` | 先确认静态契约；再分别核对上方四轴的来源。`static` 通过不表示真实 runtime 已认证，产品资格由消费方判定。 |
| 发布或升级 | `bash scripts/devkit.sh release check --summary-json` | 按 [发布与使用指南](docs/adk-usage-guide.md) 核对当前候选的验证、独立审核、精确源码及签名材料；跨版本安装显式提供 previous source，保留回滚收据。 |

以下为源码维护检查清单；每项输出只说明其检查范围：

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh target check --all --level static --summary-json
bash scripts/devkit.sh doctor --require-runtime codex --summary-json
bash scripts/devkit.sh eval run --suite deterministic --summary-json
bash scripts/devkit.sh security check --summary-json
bash scripts/devkit.sh release check --summary-json
bash scripts/check-runtime-boundary.sh
bash tests/run_all.sh --quick
```

Python package 安装（仅 ADK 构建/管理工作区，建议统一为一个隔离 venv）：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[quality]'
adk validate --strict
```

`scripts/devkit.sh` 优先显式 `ADK_PYTHON_BIN`，然后已激活的 `VIRTUAL_ENV`；否则从 `python3.12 -> python3` 选择并严格核验解释器为 3.12.x。旧 Python 3.11 venv 不可复用，不能静默回退到旧宿主；不要向纯 Skill 消费端分发构建环境。

## 6. 质量与发布原则

最小源码门禁：

```bash
bash scripts/devkit.sh validate --strict
bash scripts/check-runtime-boundary.sh
bash scripts/check-official-docs-governance.sh --summary-json
bash tests/run_all.sh
```

发布前还应执行：

```bash
python -m pip install '.[quality]'
ruff check src tools tests/fixtures/fake_target_runtime.py
mypy src/agent_dev_kit/contracts src/agent_dev_kit/evidence src/agent_dev_kit/target_adapters src/agent_dev_kit/distribution src/agent_dev_kit/execution_policy src/agent_dev_kit/versioning.py
pip-audit --strict --progress-spinner off .
bash scripts/devkit.sh release check --summary-json
```

工具未安装、外部服务不可达或真实运行时证据缺失时必须报告 `unavailable / blocked / not_required`，不能把未执行记为通过。

## 7. 维护原则

- 优先增强现有 bounded context，不再通过新增 `*_support.py` 规避模块预算。
- 文件大小只是保护线；后续架构判断以 bounded context、dependency direction、import fan-out、public API surface 和 responsibility 为主。
- Source / Release / Runtime / Product 四种状态不得互相继承。
- 外部资料可保留来源平台名称和 citation metadata，但提升为 ADK rule 时必须转换成平台中立契约。
- 没有 fresh evidence，不声明“已发布”“已认证”“已在生产可用”。

## 8. 文档入口

- `docs/commands.md`：CLI/命令参考。
- `docs/usage.md`：常用工作流。
- `docs/adk-usage-guide.md`：使用者指南。
- `docs/runbooks/workspace-maintenance-guide.md`：维护与发布检查。
- `docs/runbooks/codex-team-runtime-distribution.md`：ADK → Codex 分发链。
- `docs/runbooks/mcp-governance.md`：MCP/plugin/automation 准入。
- `docs/architecture/interoperability-boundaries.md`：协议与 runtime adapter 边界。
- `docs/architecture/canonical-change-authority.md`：ADK Canonical Change Contract 的唯一权威与兼容边界决策。

核心规则保持不变：**没有命令级、可重放的证据，不把状态升级为完成、发布、认证或生产可用。**
