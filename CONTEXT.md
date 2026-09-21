# CONTEXT.md — agent-dev-kit 领域语言定义

> 文档状态：受机器门禁约束的领域上下文投影
> 产品版本：7.0.5
> 结构化单一事实源：`manifest.json`

---

## 1. 核心概念

### 1.1 Agent

Agent 是面向稳定职责边界的执行角色。Agent 负责在授权范围内读取上下文、选择或组合 Skill、调用工具、产生证据并把结果交接给下一个职责主体。

- 结构化索引：`manifest.json:agents`
- 人类可读资产：`agents/<name>/AGENTS.md`
- Agent 不等于运行时 session；ADK 不实现通用 LLM 推理循环或 session scheduler。

### 1.2 Skill

Skill 是可复用、可版本化的方法与岗位 SOP，定义触发、非触发、输入、输出、约束、工作流、质量门禁和失败收口。

- Core Skill：`skills/<name>/SKILL.md`
- Optional Skill：`optional-skills/<name>/SKILL.md`
- 结构化索引：`manifest.json:skills` / `manifest.json:optional_skills`

### 1.3 Sub-agent

Sub-agent 是运行时创建的短生命周期执行实例，只处理边界明确、可独立验证的子任务。ADK 只定义 worker contract、权限和交接要求，不拥有具体运行时的 sub-agent scheduler。

### 1.4 Profile

Profile 是 Agent 与 Skill 的可安装组合，面向具体工作场景。

- 结构化单一事实源：`manifest.json:profiles`
- 当前主要 Profile：`core`、`personal-core`、`embedded-fullstack`、`team-core`、`release-hardening`、`large-refactor`、`incident-response`、`research-intake`

### 1.5 Manifest

`manifest.json` 是 Agent、Skill、Profile、Workflow、Target、Routing 与治理元数据的唯一结构化事实源。ADK 不再维护 Manifest 的 YAML 镜像；catalog、文档和其它视图只能从 canonical JSON 单向生成，不能成为反向写入来源。

### 1.6 Workflow

Workflow 是任务阶段与证据边界的可验证合同。ADK 定义流程、入口/出口、批准、回滚和 evidence contract；真正的模型推理、session 生命周期和 durable scheduler 仍由外部 runtime 拥有。

### 1.7 Artifact / Gate

Artifact 是任务过程中产生、可被后续阶段消费或审计的结构化产物；Gate 是对 Artifact、Evidence、权限和状态执行的 fail-closed 判定。Gate 只能证明其声明的证据等级，不能把 source/test 结果升级成 runtime/field 事实。

### 1.8 MCP / Tool / Target Adapter

- Tool/MCP：外部确定性能力接口，必须声明 transport、权限、读写/破坏性边界、数据分类和失败语义。
- Tool Target：ADK 资产可以编译/导出的运行时目标。
- Target Adapter：负责静态转换、安装计划和边界验证，不把“导出成功”冒充“原生运行时已验证”。

### 1.9 Evidence / Receipt

Evidence 是可验证事实；Receipt 是某次确定性执行产生的机器可读证明。二者必须绑定 source identity、命令/动作、结果、时间、新鲜度与环境，历史报告不得覆盖更新的失败或 stale 状态。

---

## 2. 产品边界

ADK 的定位是平台中立的 Agent 资产编译、安装、评测和发布控制面。

ADK 负责：

1. Agent/Skill/Profile/Workflow/Target 的结构化建模。
2. Routing IR、上下文治理与权限边界。
3. 编译、导出、安装计划、回滚和静态 target validation。
4. Evidence、Run Evidence、Effect Comparator、campaign 与 release contract。
5. 官方资料 freshness、供应链和发布门禁。

ADK 不负责：

1. 通用 LLM inference loop。
2. 生产 session scheduler、issue polling 或 workspace lifecycle daemon。
3. 默认写入任意用户 runtime 目录。
4. 未经 owner review 自动启用 MCP、Hook、Plugin 或 Automation。
5. 用 fixture、静态导出或 owner attestation 冒充 native runtime / field evidence。

---

## 3. Routing 与任务模式

Routing 的机器事实位于 `manifest.json:routing`，当前 IR 为 `routing-ir/v2`。核心字段包括：

- `task_mode`
- `intent`
- `negated_intents`
- `mutation_permission`
- `risk`
- `profile_availability`
- `required_evidence`
- `abstain`

只读、实现、调试、评审和发布必须先由 task mode 决定 mutation permission。LLM 分类结果本身不得直接成为写入或发布授权。

---

## 4. Context 与 Knowledge

知识层保持 L0-L4：toolchain、general-tech、domain、project、session。上下文采用渐进加载：稳定规则优先，阶段性 Skill 按需加载，历史证据只在必要时检索。Session 临时状态不是长期知识，也不应进入版本化产品事实。

---

## 5. 嵌入式领域边界

嵌入式能力通过 `embedded-fullstack` profile 承载，包括 SoC/MCU/MPU、Boot/BSP、Linux/RTOS/bare-metal、驱动/DMA/中断、协议栈、HIL/SIL、产测、OTA、RMA 与现场恢复。嵌入式经验不能被提升为通用 `core` invariant。

常用术语：BSP、RTOS、MCU、HIL、SIL、DMA、ISR、OTA、RMA。

---

## 6. 质量与证据等级

### Quality Tier

- P0：核心主干资产，必须具备可执行流程与验收证据。
- P1：稳定扩展资产，必须具备命令、样例和质量门禁。
- P2：可选场景资产，必须具备边界说明和最小验证路径。

### 证据层

- source：源码/manifest/contract 事实。
- test：确定性测试和静态验证。
- runtime：真实目标运行时 discovery/load/trigger/rollback 等证据。
- field：真实仓、真实操作者、真实周期和现场结果。

高层证据不能由低层证据自动推导。

---

## 7. 结构化 SSOT 与派生物

| 信息 | 单一事实源 | 派生投影 |
|---|---|---|
| 产品版本与资产索引 | `manifest.json` | README、catalog |
| Agent | `manifest.json:agents` + `agents/` | target bundle |
| Skill | `manifest.json:skills/optional_skills` + Skill 文件 | catalog/target bundle |
| Profile | `manifest.json:profiles` | catalog |
| Workflow | `manifest.json:workflows` + `workflows/` | Workflow 文档投影 |
| Routing | `manifest.json:routing` | routing matrix/catalog/tests |
| Target | `manifest.json:tool_targets` + target contracts | export/install plan |
| Release identity | exact commit/tree + manifest/release receipt | release notes |

派生文件与 SSOT 不一致时必须 fail closed；不得靠人工解释覆盖机器事实。Manifest 不允许第二结构化镜像。

---

## 8. 验证要求

最小开发验证：

```bash
rtk scripts/devkit.sh validate --strict
rtk tests/run_all.sh
```

发布/认证验证必须使用 Python 3.11+，并补 security、release check、target contract、rollback/rehearsal 与相应 runtime/field evidence。工具未安装、凭据缺失或外部数据不可得时必须标记 unavailable/blocked，不能记录为 pass。

---

## 9. 文档与变更治理

非平凡实现、长任务、失败恢复或 Gate 变更应使用 `docs/changes/<id>/` 保存 requirements、design、tasks、negative-results 与 verification evidence。历史变更文档允许出现被移除的外部仓、旧路径或负结果，这类 provenance 不得被误判为 active runtime dependency。

---

## 10. 版本与发布

版本身份必须至少绑定：SemVer、exact commit、tree、manifest digest 与验证/发布 receipt。`manifest.json` 是版本 SSOT；其它文件只做受门禁约束的只读投影。手工 workflow dispatch 产生的候选不得自动获得正式 release 身份。

受保护 `main` 采用 auto-promotion 发布模型：PR 在合并前必须让 source SemVer 相对 exact base 严格前移；successful-main CI 后自动创建 exact-SHA annotated tag 和 GitHub Release。同版本旧 tag 指向不同 commit 是 blocker，不能等合并后再作为正常状态处理。

---

## 11. 安全要求

- 禁止硬编码密钥、token 和客户敏感数据。
- 默认最小权限；破坏性动作必须显式授权并有回滚。
- 外部 source / MCP / Plugin / Hook / Automation 默认不进入 active runtime。
- 依赖与 GitHub Actions 使用版本锁定/不可变 SHA，并保留供应链审计证据。

---

## 12. 使用规范

1. 先读 `AGENTS.md` 与目标目录局部规则。
2. 所有结构化资产修改只编辑 `manifest.json`；不得新增平行 Manifest 镜像。
3. 行为变化必须增加确定性测试和相邻负例。
4. 只读任务不得因为“长任务”“发布”“调试”等词汇自动扩大 mutation permission。
5. 没有 fresh evidence 不声明可发布、可安装、可合并或生产可用。
6. 不直接把 ADK 资产写入未声明 runtime；必须经过 target/source-to-live 与 rollback 治理。
7. 不把 cache、session state、raw prompt、raw log 当长期产品事实。
