# Artifact-Gated Delivery Runbook

## 1. 场景适用

- 变更涉及共享契约、发布链路或跨角色交接。
- 需要统一产物标签和门禁结果，避免"口头完成"。

## 2. 推荐能力组合

- Profile：`core + adk-artifact-gated-lite`
- Optional Skill：`adk-artifact-gated-lite`
- 必备技能：`adk-verification-before-completion`、`adk-commit-pr-quality-gate`

## 3. 执行步骤

1. 安装能力组合：
   ```bash
   bash scripts/devkit.sh install --tool codex --profile core --extra-profile adk-artifact-gated-lite --with-optional-skill adk-artifact-gated-lite
   ```
2. 创建变更工件并进入 `propose -> apply`。
3. 在变更工件中补齐三类标签：
   - `[artifact:ImplementationPlan]`
   - `[artifact:ReviewReport]`
   - `[artifact:TestReport]`
4. 执行 `verify`，记录真实命令输出。
5. 执行 `review`，确保与标签化结论一致后再归档（`workflow.sh` 会自动校验一致性）。

## 4. 最小标签模板

```md
[artifact:ImplementationPlan]
status: READY
owner: <agent>
scope:
- <范围>
handoff_to:
- <next-owner>

[artifact:ReviewReport]
status: PASS
verdict: pass | needs-fix

[artifact:TestReport]
status: PASS
tests_run:
- <command + result>
```

## 5. 失败与升级

- 缺失标签或证据：结论必须 `needs-fix`，禁止归档。
- 发现共享契约影响未评估：升级到架构评审再继续。

---

## 附录：完整 Artifact-Gated 协议规范

> 以下内容源自 `artifact-gated-agents` 参考仓库的完整多角色协作协议，供需要完整 artifact 标签体系和角色矩阵时查阅。

### 总则

1. **Artifact First**：所有阶段只认标准产物，不以口头结论代替交付。
2. **Gate Before Build**：未满足入口条件的 agent 不得越过门禁进入实现。
3. **One Role, One Decision**：关键决策必须有唯一主责角色。
4. **Read-Only Reviewers**：评审、审批、安全角色默认只读。
5. **Traceable Delivery**：每段实现都必须能追溯到需求、设计、架构、测试依据。

### 标准 Artifact 标签

禁止使用同义词或中文别名，统一使用以下标签：

| 类别 | 标签 | 说明 |
| :--- | :--- | :--- |
| 产品 | `[artifact:PRD]` | 背景、目标、范围、约束、验收标准 |
| 产品 | `[artifact:UserStory]` | 角色、场景、价值、验收条件 |
| 产品 | `[artifact:Prototype]` | 页面结构、交互流程、状态与异常流 |
| 设计 | `[artifact:DesignSpec]` | Token、视觉规范、组件规则、响应式要求 |
| 设计 | `[artifact:UICode]` | HTML/CSS 原型或高保真实现稿 |
| 设计 | `[artifact:InteractionSpec]` | 状态切换、反馈、动画、空态/错态说明 |
| 架构 | `[artifact:SystemArch]` | 系统边界、模块职责、依赖与数据流 |
| 架构 | `[artifact:DBDesign]` | ER、表结构、约束、索引、迁移策略 |
| 架构 | `[artifact:APIDoc]` | 接口契约、字段、鉴权、错误码 |
| 架构 | `[artifact:TaskBreakdown]` | 面向实现层的任务拆解、依赖与边界 |
| 开发 | `[artifact:ImplementationPlan]` | 目标、改动范围、实现步骤、风险、验证计划 |
| 开发 | `[artifact:FrontendCode]` | 前端实现结果与验证说明 |
| 开发 | `[artifact:BackendCode]` | 后端实现结果与验证说明 |
| 开发 | `[artifact:AICode]` | Prompt、RAG、工作流、模型集成实现 |
| 质量 | `[artifact:Approval]` | 审批结论，仅允许 `APPROVED` / `REJECTED` |
| 质量 | `[artifact:ReviewReport]` | 代码/设计/架构评审结果 |
| 质量 | `[artifact:TestCase]` | 功能、边界、异常、回归用例 |
| 质量 | `[artifact:TestReport]` | 测试结果、阻断项、残余风险 |
| 安全 | `[artifact:SecurityReport]` | 权限、依赖、数据安全与攻击面审计 |
| 运维 | `[artifact:DeploymentPlan]` | 构建、部署、回滚、监控与发布说明 |

### 统一执行协议

#### 入口检查

每个 agent 开工前必须显式检查：
- 当前任务目标是否明确
- 必需 artifact 是否齐备
- 本角色是否有权限处理该任务
- 是否存在上游审批或评审前置条件

如果任一条件不满足，必须返回 `BLOCKED`，不得自行脑补上游产物后继续推进。

#### 通用输出头

除 `Approval` 外，所有 artifact 输出都必须包含以下头部字段：

```md
[artifact:<Tag>]
status: READY | BLOCKED | PASS | FAIL
owner: <agent-name>
scope:
- <本次处理范围>
inputs:
- <使用到的上游 artifact 或上下文>
handoff_to:
- <下一个责任角色>
```

#### 阻塞模板

```md
[artifact:<Tag>]
status: BLOCKED
owner: <agent-name>
scope:
- <希望完成但尚未能执行的工作>
missing_inputs:
- <缺失的 artifact 或上下文>
blocking_reasons:
- <为什么不能继续>
handoff_to:
- <应补齐该输入的角色>
next_action:
- <上游补齐后如何重新进入流程>
```

#### 交付模板

```md
[artifact:<Tag>]
status: READY
owner: <agent-name>
scope:
- <本次交付范围>
inputs:
- <使用到的输入>
deliverables:
- <产物核心内容摘要>
risks:
- <剩余风险；没有则写 None>
handoff_to:
- <下游角色>
exit_criteria:
- <本阶段完成标准>
```

#### 专项模板

`[artifact:Approval]` 必须使用：

```md
[artifact:Approval]
result: APPROVED | REJECTED
owner: engineering-manager
scope:
- <审批范围>
required_inputs:
- <审查过的输入>
checklist:
- [x] PRD/Prototype 已齐备
- [x] 设计或架构产物已齐备
- [x] TaskBreakdown 已齐备
- [x] 实施范围清晰
- [x] 风险可控
blocking_issues:
- <阻断问题；没有则写 None>
approved_scope:
- <允许进入实现的范围；拒绝时写 None>
handoff_to:
- <实现角色或返回上游角色>
```

`[artifact:ReviewReport]` / `[artifact:SecurityReport]` / `[artifact:TestReport]` 必须包含：

```md
verdict: PASS | FAIL
findings:
- [severity:blocker|high|medium|low] <问题>
must_fix:
- <发布前必须修复的问题；没有则写 None>
can_follow_up:
- <允许后续处理的问题；没有则写 None>
```

### 角色矩阵

#### 产品与决策层

- `senior-ai-agent-pm`
  - 输入：用户需求、业务上下文
  - 输出：`[artifact:PRD]`、`[artifact:UserStory]`、`[artifact:Prototype]`
  - 禁止：直接编写业务实现代码
  - 交接：`senior-ui-designer`、`tech-lead-architect`

- `tech-lead-architect`
  - 输入：`[artifact:PRD]`、`[artifact:Prototype]`，必要时参考设计稿
  - 输出：`[artifact:SystemArch]`、`[artifact:DBDesign]`、`[artifact:APIDoc]`、`[artifact:TaskBreakdown]`
  - 禁止：绕过实现层直接完成主要业务实现
  - 交接：`engineering-manager`、实现层

- `engineering-manager`
  - 输入：上游产品、设计、架构、任务拆解产物
  - 输出：`[artifact:Approval]`
  - 禁止：跳过门禁直接放行编码
  - 交接：实现层或退回上游补齐

#### 设计与实现层

- `senior-ui-designer` → 输入 PRD/Prototype，输出 DesignSpec/UICode/InteractionSpec
- `senior-frontend-engineer` → 输入 TaskBreakdown/DesignSpec/UICode/APIDoc/Approval，输出 ImplementationPlan/FrontendCode
- `senior-backend-engineer` → 输入 TaskBreakdown/SystemArch/DBDesign/APIDoc/Approval，输出 ImplementationPlan/BackendCode
- `ai-engineer` → 输入 PRD/Prototype/SystemArch/Approval，输出 ImplementationPlan/AICode

#### 评审与质量层

- `code-reviewer` → 默认只读，输出 ReviewReport
- `system-designer` → 默认只读，输出 ReviewReport
- `security-engineer` → 默认只读，输出 SecurityReport
- `senior-qa-engineer` → 输出 TestCase/TestReport
- `devops-engineer` → 输出 DeploymentPlan

### 阶段入口/出口条件

| 阶段 | 主责角色 | 入口条件 | 输出 | 出口条件 | 下一角色 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Product | `senior-ai-agent-pm` | 需求或问题陈述存在 | `PRD` `UserStory` `Prototype` | 范围、目标、验收标准明确 | `senior-ui-designer` `tech-lead-architect` |
| Design | `senior-ui-designer` | `PRD` `Prototype` 齐备 | `DesignSpec` `UICode` `InteractionSpec` | 关键页面、状态、组件规则齐备 | `tech-lead-architect` `engineering-manager` |
| Architecture | `tech-lead-architect` | `PRD` `Prototype` 齐备 | `SystemArch` `DBDesign` `APIDoc` `TaskBreakdown` | 模块边界、接口、任务拆解清晰 | `engineering-manager` |
| Approval | `engineering-manager` | 产品、设计/架构、任务拆解齐备 | `Approval` | 结果为 `APPROVED` 或 `REJECTED` | 实现层或上游 |
| Implementation | 实现层 | `Approval=APPROVED` 且必需输入完整 | `ImplementationPlan` `FrontendCode/BackendCode/AICode` | 代码完成且自检说明齐备 | Review / Security / QA |
| Review | `code-reviewer` `system-designer` | 代码或设计产物已提交 | `ReviewReport` | 阻断问题已识别 | QA / 实现层 |
| Security | `security-engineer` | 架构/接口/代码可审查 | `SecurityReport` | 高危问题结论明确 | QA / 实现层 |
| QA | `senior-qa-engineer` | 代码与契约可验证 | `TestCase` `TestReport` | 关键路径测试结论明确 | `devops-engineer` |
| Release | `devops-engineer` | Review/Security/Test 无阻断 | `DeploymentPlan` | 部署、回滚、监控方案齐备 | 发布执行 |

### 编码前置门禁

实现层开工前必须全部满足：
- 存在 `[artifact:PRD]`
- 存在与任务相关的设计或架构产物
- 存在 `[artifact:TaskBreakdown]`
- 存在 `[artifact:Approval]` 且结果为 `APPROVED`

紧急缺陷修复例外：可跳过完整产品链路，但必须补齐最小 ImplementationPlan、ReviewReport 和 TestReport。

### 审批与发布检查清单

审批时必须逐项确认：目标/范围/验收标准明确、关键交互已定义、API/数据契约明确、任务拆解到可执行粒度、风险和依赖已说明、实现范围未越权扩张。

发布前必须满足：Approval=APPROVED、ReviewReport 无 blocker、SecurityReport 无高危未决、TestReport 关键路径通过、DeploymentPlan 含回滚方案。
