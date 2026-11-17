# Workflow Skill 独立可用性审查

## 结论与证据等级

冻结基线：`78c3be7f6f9b5ee2e557de54156532fb3169198d`，source version `11.3.13`。审查者职责为只读审查，未修改仓库资产、未提交、未 push、未操作 live runtime、未外发消息。

本组 **25 个 Skill 全部完成全文审查**，并读完它们的 **35 个 Markdown 辅助文件**。原文共 1,608 行、92,990 字节；该计数仅描述输入范围，不是 Token 或效率测量。逐 Skill 显式作用域正例 25/25、反例 25/25 通过；真实 compiler 的 Claude Code 与 OpenCode 导出均包含本组 25 个 Skill；全部 `references/` 文件随包保留。53 个既有定向测试通过。

发现四项可重放问题：机器任务包字段与封闭接收合同冲突、畸形任务包使 validator 抛异常、中文代码评审被提交门禁误选、通用诊断/回滚被嵌入式量产入口误选。前两项由实际源码 validator 调用复现，后两项由实际生产 matcher 复现。它们均不是 native LLM/宿主执行结果；实际模型行为、真实任务端到端成功率、Token、时延和产品资格全部 `not-measured / not-run`。

未发现证据支持把 human approval 与委派 AI 审查简单判为冲突；该候选已明确排除。没有为了凑覆盖率或修改数量提出额外规则、Skill、Gate 或统一长模板。

## 可重放入口

运行时只读源仓，生成物位于本报告目录：

```bash
/workspace/scratch/fe8de3b42084/verification-tools/rtk bypass env PYTHONDONTWRITEBYTECODE=1 python3 -B /workspace/scratch/fe8de3b42084/skill-usability-audit/workflow/reproduce.py
```

`reproduce.py` 固定核验上述 HEAD，并仅替换自身的 `workflow/exports/` 暂存导出。它调用真实 `Manifest.load`、`match_text`、`export_assets` 和 `validate_task_package`，不复制模拟这些实现。

| 文件 | 证据内容 |
|---|---|
| `source-inventory.json` | 25 个原文的 SHA256、行数/字节数、完整读取辅助文件表、逐 Skill 显式正反路由回执 |
| `identity.json` | 基线 HEAD、version、Python 身份、执行前后 Git 状态 |
| `routing.json` | 自然任务输入、完整 matcher 结果、对照与额外观察 |
| `task-package-validator.json` | 合法控制、随包字段变体、禁止写研究包三个实际校验结果 |
| `task-package-malformed.json` | 四个有效 JSON 但类型错误的任务包引发的真实 Python 异常 |
| `exports.json`、`exports/` | 两个真实 target 的完整导出清单、落盘文件和依赖存在性 |
| `existing-tests.json`、`existing-tests.txt` | 53 个定向测试的 argv、退出码、耗时及原始输出 |

仓库执行前后均只有父 Agent 创建的 `docs/changes/20261117-skill-usability/{requirements,design,tasks,negative-results}.md` 为 untracked；本审查前后状态相同。没有读取其他审查者的本轮报告。

## 25 项覆盖记录

下表每一行均已完整阅读 `skills/<name>/SKILL.md`，并完成真实双 target 导出及显式正/反路由。这里的“无新增缺陷”仅指本次已检查范围，没有升级为行为认证。

| # | Skill | 读取的辅助材料与具体核验 | 结论/剩余边界 |
|---|---|---|---|
| 1 | `adk-requirements-triage` | `exploratory-requirements-brief.md`、`embedded-discovery-brief.md`；brief/execution-handoff/high-risk 的字段与退出边界；文档保真用例 | 无新增缺陷。已批准功能词仍可能先选 triage，但正文明确退出且不重复访谈，单凭选择不能声称实际多问。 |
| 2 | `adk-structured-requirements-questioning` | `prototype-as-experiment.md`；Explore 单问、Challenge 依赖 frontier、部分回答/修订、只读原型边界；现有 interactive routing fixtures | 无新增缺陷。真实多轮问答、收敛率未运行。 |
| 3 | `adk-repo-prompt-analysis` | 无独立 reference；核只读 Git/rg 入口、callsite/role/动态输入追踪、不可信源码边界 | 无新增缺陷。未提供外部候选仓，本次不虚构外部研究结果。 |
| 4 | `adk-skill-deep-analysis` | `details.md`；source-discovery/method-only/deep-audit/behavior-eval 与 implementable handoff | 无新增缺陷。条件性外部评测参考不能当已安装能力；无真实候选/宿主时已有 needs-evidence/not-measured 路径。 |
| 5 | `adk-lightweight-planning` | README；最少步骤、只读计划、已有执行任务退出、TBD 与高风险保留；文档作者测试 | 无新增缺陷。计划正文不强制固定步数/时长。 |
| 6 | `adk-task-breakdown` | `vertical-slice-planning.md`、`task-packaging.md`；真实 expand/migrate/contract 正反例；v2 validator、实际导出 | **W-01、W-02**。纵向迁移示例正反用例通过；机器包失败不能由这些方法示例的通过掩盖。 |
| 7 | `adk-interface-contract-design` | 全部五份 reference；JSON Schema draft 闭合、C 版本/能力例、生命周期、工具副作用、Spec↔Code | 无新增缺陷。5 个 schema 用例与实际 C 版本能力例通过；目标 wire/ABI 与设备生命周期仍须真实目标证据。 |
| 8 | `adk-adr-writer` | 无 reference；真实决定/单路径、定向修订、reader-only acceptance、文档保真 | 方法正文无新增缺陷。另有动作/主题多意图路由观察 O-01，未并入四项实施范围。 |
| 9 | `adk-component-api-stability` | 无 reference；旧源码、新头文件、旧 object/executable、类型信息、ABI 工具退出状态及 runner 边界 | 无新增缺陷。没有真实旧新库/消费者输入，因此 ABI 与目标运行记未运行。 |
| 10 | `adk-code-simplification` | `details.md`、`deep-module-design.md`；尤其检查早返回、cleanup、资源顺序及不滥加抽象 | 无新增缺陷。例中的条件合并保留后续 cleanup；没有源项目简化任务，不宣称完成实际重构或性能改善。 |
| 11 | `adk-systematic-debugging` | 全部三份 reference；真实 Git bisect 的 good/bad/skip/infra-abort、UBSan recover/fatal/fixed、跨层分流 | 方法正反例通过。作为 **W-04** 的正确通用诊断 owner，需要接收通用诊断意图，但不扩大写/设备权限。 |
| 12 | `adk-offline-core-dump-triage` | 无 reference；binary/BuildID/库关联、GDB -nx/auto-load、sysroot 与可信帧边界 | 无新增缺陷。没有 dump、匹配二进制或目标 GDB，不将命令静态可读判为可信 backtrace。 |
| 13 | `adk-test-strategy` | `high-value-tdd.md`；独立 expected、实际错误变体、并行资源与只读策略/实施交接 | oracle 镜像漏报对照、独立错误拒绝与正确实现通过均实跑。一般 Python 补测进入只读策略是当前刻意边界，未声称模型因此停工。 |
| 14 | `adk-artifact-gating` | `details.md`；READY/PASS 与 workflow stage 分离、PASS/PASS/verdict 一致、签收不代替验证 | 无新增缺陷。真实导出确认 llm_agent Root helper 被条件化，不要求普通 consumer 安装不存在脚本。 |
| 15 | `adk-pilot-framework` | `details.md`；smoke 与收益比较、pilot-fail/blocked/inconclusive 分离、目标健康检查适用性 | 无新增缺陷。没有真实 target 试跑，本次不生成 pilot-pass。 |
| 16 | `adk-verification-before-completion` | `verification-governance-details.md`；checkpoint/goal-final、25 步按影响加载、checker 校准正常/违规/错误/缺覆盖 | checker 实例正反运行通过。文档明确示例不为生产 gate，未把缺少额外泛化 parser 特性扩成缺陷。 |
| 17 | `adk-code-review-loop` | 全部四份 reference；raw diff、staged/working-tree/branch、overlay、只读索引、textconv/ext-diff/fsmonitor/submodule 对照 | raw diff 与快照用例通过；**W-03** 是入口所有权缺口，不是已验证 review 方法错误。 |
| 18 | `adk-repo-drift-remediation` | README；先 issue map、保留 dirty、共享触点串行、ADK CLI 源根限定、read-only Git status | 无新增缺陷。status preflight 的无索引写/FSMonitor 控制经既有测试实跑。 |
| 19 | `adk-commit-pr-quality-gate` | `pr-risk-gates.md`；message-only/PR-readiness/high-risk 适用性、SCM 独立授权 | **W-03**。message-only 控制正确；“代码评审”落入不承担独立 review 的 Skill。 |
| 20 | `adk-release-versioning` | `details.md`；真实临时 Git 仓的首发、正式基线、breaking/revert/unknown、shallow、非法 ref、空范围 | 5 项 release-history 测试通过，无新增缺陷。仅隔离 fixture 历史，不创建实际项目 tag/Release。 |
| 21 | `adk-production-field-readiness` | `pilot-measurement-evidence.md`；实机证据/OTA回滚/现场诊断、wall-clock 与 person-minutes 分离、实际 auto route | **W-04**。正确现场入口控制通过；没有真实现场材料，不签 ready。 |
| 22 | `adk-cross-team-handoff` | 无 reference；lite/formal、真实 owner/receiver、cold-read、pending/accepted、签收不代表权限切换 | 方法正文无新增缺陷。自然任务在 ADK matcher 被 supporting explicit-only 拒绝，属现有刻意策略；观察 O-02 单列。 |
| 23 | `adk-branch-closeout` | `closeout-options.md`；单一操作、授权延续、未知写结果先对账、fresh-main、保留默认 | 无新增缺陷。未经实际 SCM/CI 不宣称创建/合并；Draft PR 与 PR-only CI 的潜在流程问题未取得项目特定要求，不作为缺陷。 |
| 24 | `adk-after-action-review` | 全部三份 reference；lite/promotion、模板副本与 canonical 字节一致、候选/批准/写入分别记录 | 无新增缺陷。human approval 候选已排除；导出中有本地同义模板，不能仅因根 templates 缺失报导出缺陷。 |
| 25 | `adk-engineering-growth-review` | README、`growth-evidence-boundaries.md`；index-first、授权范围、跨时点证据、普通建议/长期晋级区分 | 无新增缺陷。metadata 与 body 的晋级范围已有测试保护；未读用户全历史或请求外部课程。 |

## W-01 — 机器任务包字段清单与真实封闭 v2 合同互相冲突

**级别：major；类型：静态发布合同矛盾 + 已复现的源码 validator 拒绝。**

### 位置与片段

- `skills/adk-task-breakdown/SKILL.md:33` 要求 machine-dispatched 使用完整 `adk-task-package-schema-v2`，`:38` 要划清 scope/interface，`:47` 要求 v2 与 ready_to_handoff 不可省。
- `skills/adk-task-breakdown/references/task-packaging.md:7` 将这些项目置于同一 v2 字段清单：

```text
For machine-dispatched work: adk-task-package-schema-v2 with ...
global_constraints, interfaces, scope_read, scope_write, ready_to_handoff.
```

- `src/agent_dev_kit/intent_boundary.py:14-34` 的 `TASK_REQUIRED_FIELDS` 为封闭的 19 个字段，不含上述五项；`:82-89` 拒绝所有额外字段。
- `manifests/structured_output_contracts.json` 同样 `additional_properties:false`，其 19 字段合同与 validator 一致。

### 任务与实际结果

真实任务形态：“把一个已经获准的只读超时边界研究拆成机器任务包，写明只可读 `src/retry.py`、禁止写、接口、全局约束与是否 ready”。

`reproduce.py:task_contract` 先构造当前 canonical 接受的 research 包，返回 `[]`；仅加入随包 reference 明列的五字段，返回：

```text
unexpected fields: global_constraints,interfaces,ready_to_handoff,scope_read,scope_write
```

真实 compiler 在 Claude Code、OpenCode 两个导出中保留该 reference 原文。两个包内 v2 标识仅出现在 task-breakdown 正文与此 reference；没有 `manifests/structured_output_contracts.json`、`intent_boundary.py` 或 task-breakdown canonical 模板。不能要求纯 Skill consumer 回仓库猜完整字段与嵌套位置。

### 影响与测试缺口

按随包方法直接生成顶层机器对象会被 ADK 当前 v2 validator 拒绝；删掉安全边界字段又不能解释应放在哪里，导致交接退回或自行发明合同。该问题不是写权限扩大；合法控制中的研究权限仍为 forbidden。

`tests/test_skill_method_efficiency.py:44-49` 只断言标识/字段名存在；`tests/test_intent_boundary_governance.sh`、`tests/test_superagent_method_contract.py` 使用手写 canonical fixture，不消费随包字段说明。现有 standalone export 用例覆盖 context、parallel-worker 和 AAR，但不校验 task-breakdown 发布方法产生的对象。

### 最小修复草案

保留唯一 v2 合同与现有拒绝未知字段，不放宽 validator、不另建 schema 版本。改写现有 `task-packaging.md`：给出完整 19 个允许顶层字段、必要类型/枚举与跨字段规则；明确 `scope_read/scope_write/global_constraints/interfaces` 的可读表达映射到 canonical `constraints` 字符串条目，或归已有独立 worker envelope，禁止塞进 v2 顶层。`ready_to_handoff` 是调度派生判定，说明与 v2 payload 分离。可用一个紧凑合法 research 示例代替当前模糊字段串，不增加全局默认上下文。

从实际导出的示例提取 JSON 并交当前 `validate_task_package`；没有本地接收 validator 的纯 consumer 应说明校验状态，不冒充机器验证。

### 正反验收

- 正：Claude/OpenCode 实际导出的完整 research 与 approved implementation 示例被原 validator 接受；完整范围/接口/约束语义仍存在且不授新权限。
- 正：prototype 使用 `prototype_evidence:<path>`，通过正确 gate/permission 组合；合法已通过路径保持。
- 反：五个 envelope/派生字段放入 v2 顶层仍拒绝；未知字段、旧 v1、缺必需字段拒绝。
- 反：research/decision/prototype 设置 approved、错误 exit_gate、prototype 缺证据拒绝。
- 边界：人工 brief 不强制机器包；实际运行时调度及模型遵从性不由该测试认证。

## W-02 — v2 validator 对类型错误输入抛异常，未返回可交接的拒绝原因

**级别：major；类型：已复现的 Python 源码 API 失败。关联 Skill：task-breakdown 的机器交接能力。**

### 位置与片段

`src/agent_dev_kit/intent_boundary.py:109-129` 对 artifacts 的类型只追加 error，随后无条件迭代/调用字符串方法；对 kind 与 retention 无字符串检查即进行 dict/set membership：

```python
if not _non_empty_string_list(value[field]):
    errors.append(...)
kind = value["work_item_kind"]
if kind not in WORK_ITEM_RULES:
    ...
prototype_refs = [item.partition(":")[2]
                  for item in value["artifacts"]
                  if item.startswith("prototype_evidence:")]
if value["retention_decision"] not in RETENTION_DECISIONS:
    ...
```

函数签名为 `validate_task_package(value: Any) -> Tuple[str, ...]`，已对非 object 和缺字段采取返回错误的行为。Skill 和 structured-output contract 要求不合法输出走 blocked/replan/refusal handling。

### 任务与实际结果

同一研究交接包来自 JSON 解析，模型/上游把 artifact 路径误填数字、缺值填 null，或将枚举填数组。只替换一个字段：

| 单变量输入 | 实际结果 |
|---|---|
| `artifacts:[1]` | `AttributeError: 'int' object has no attribute 'startswith'` |
| `artifacts:null` | `TypeError: 'NoneType' object is not iterable` |
| `work_item_kind:[]` | `TypeError: unhashable type: 'list'` |
| `retention_decision:[]` | `TypeError: unhashable type: 'list'` |

完整输入与异常见 `task-package-malformed.json`；均为实际 validator 调用。当前检索到的调用方主要是源仓治理/回归代码，**没有观测 live dispatcher 崩溃**。

### 影响与测试缺口

对格式合法但 schema 不合法的 JSON，调用者无法得到预期的结构错误列表；若沿原返回值契约做 blocked/replan，会被意外异常打断。没有证据表明可因此绕过权限，不能夸大为安全放行。

既有 v2 用例集中于缺字段、旧版本、权限/gate、prototype证据；未覆盖类型不合法但字段齐全的组合。

### 最小修复草案与正反验收

仅在现有 validator 内调整类型验证顺序：先确认枚举值为 string；artifacts 已确认非空 string list 后才查 prototype ref；类型不合法时返回已有/新增的字段错误，不进入依赖该类型的交叉检查。保留封闭字段、原合法数据和跨字段拒绝，不用宽泛 `except Exception` 把编程错误变成功。

- 正：canonical research、decision、implementation、prototype 继续返回空 tuple。
- 反：上表四项和相同字段的 object、bool、number、空字符串组合返回非空 tuple，无异常。
- 反：研究包 approved、错误 gate、prototype 无证据仍被拒绝。
- 反：缺字段、额外字段、非 dict 输入维持原错误合同；不得 coercion 为合法字符串。

## W-03 — “代码评审”被交给声明不能替代独立审查的提交门禁

**级别：major；类型：已复现的 deterministic Skill 选择错误。**

### 位置与片段

- `skills/adk-commit-pr-quality-gate/SKILL.md:12` 仍声明 trigger `代码评审`，但 `:3/:28` 明确“不能替代独立代码审查”。
- `skills/adk-code-review-loop/SKILL.md:45-50` 已提供 feedback-triage、完整独立审查和门禁交接方法。
- `manifest.json:2646-2650` 的 `code_review_loop` intent 含 `代码审查`、`审查反馈` 等，不含 `代码评审`。

### 任务与实际结果

| 用户请求 | 实际 primary / source | 正确职责 |
|---|---|---|
| 请帮我做代码评审 | commit-pr-quality-gate / skill_trigger | code-review-loop |
| 请核实这条代码评审意见，不修改代码 | commit-pr-quality-gate / skill_trigger | code-review-loop 的 feedback-triage |
| 请进行独立代码审查（控制） | code-review-loop / routing | 保留 |
| 请校验 commit message（控制） | commit-pr-quality-gate / routing | 保留 |

两项误选均保持 `mutation_permission=deny`；反馈请求的 `task_mode=readonly`、`execution_effort=E0` 正常。本 finding 只针对 primary owner，不把 IR 模式/权限误报为失败。

### 影响与测试缺口

自然中文同义词把语义审查/单条反馈核验交给只核提交证据的 Skill；其正文不能交付已请求的 review，或要求无关 PR/readiness 材料。未运行真实模型，因此不能宣称已观察到全仓重审或实际延迟。

当前 trigger fixture 对 commit 主要使用提交/commit message；review 主要使用“审查”和英文 review。description 区分测试仅验证词存在，未做“代码评审” auto 两 owner 碰撞。

### 最小修复草案与正反验收

把“代码评审”同义入口从 commit Skill 移至既有 code-review-loop Skill 与其 manifest intent；保留 commit-only/message-only 所有者。使用现有路由机制，不增加第二个 review Skill 或新权限规则。

- 正：上述两条和“只核实这条代码评审反馈”选择 code-review-loop；反馈内容由现有 feedback-triage 判断，不要求完整 PR。
- 正：commit message、提交前检查、实际 PR 准入仍由 commit gate；原独立代码审查仍选择 review。
- 反：“不要做代码评审，只校验 commit message”不可选 review。
- 反：review/feedback 不授予文件写入、SCM comment、commit/merge 权限。

## W-04 — 通用“诊断/回滚/设备状态机”抢占嵌入式量产入口

**级别：major；类型：已复现的 deterministic 领域适用性错误。**

### 位置与片段

- `skills/adk-production-field-readiness/SKILL.md:10/:13/:19-21` 含无领域约束的 `诊断`、`回滚`、`simulate-device/模拟设备/设备状态机`。
- `manifest.json:2777-2783` 的 production_field_readiness intent 同样接受裸词。
- Skill `:25-32/:41-54` 要求设备型号、硬件版本、BOM、烧录/产测、OTA、现场维护证据。这些不是普通 Python/Web/DB 任务输入。

### 任务与实际结果

| 请求 | 实际 primary | 判断 |
|---|---|---|
| 诊断这个 Python 脚本的异常 | production-field-readiness | 应进入通用 systematic-debugging |
| 先诊断 Web API 超时的根因 | production-field-readiness | 应进入通用 systematic-debugging |
| 请检查数据库回滚方案 | production-field-readiness | 不得假设设备量产；可按已有契约设计入口或 abstain |
| 帮我设计设备状态机，不涉及量产或OTA | production-field-readiness | 设计任务与现场 readiness 不同，不应选择量产入口 |
| 检查嵌入式量产产测和现场维护 readiness（控制） | production-field-readiness | 应保留 |
| 请定位根因并保留最小复现（控制） | systematic-debugging | 应保留 |

所有误选保持 `mutation_permission=deny`，未发生设备动作授权。这里不是 runtime device safety failure；是通用任务被送入错误的领域前置条件与输出合同。

### 影响与测试缺口

匹配的 Skill 会要求不存在的硬件/烧录/OTA材料，并可能把正常软件分析记 blocked。源码已明确不应把未测试状态包装成 ready，但该安全边界不能修复任务入口错误。

`tests/fixtures/skill_trigger_cases.tsv:46` 将“量产产测烧录诊断 OTA 回滚和现场维护”放在同一正例，领域词掩盖裸词问题。既有 near-miss 是“通用 Web 发布”，不能覆盖 Web 诊断或 DB 回滚；新的 embedded routing tests 处理了文件系统/CMake noun，也没有覆盖本 Skill 这些泛词。

### 最小修复草案与正反验收

优先收窄 production 触发措辞到产测/现场/设备交付语义，或使用既有 implicit-context 领域条件；通用诊断由现有 systematic-debugging 接收。移除纯“设备状态机”对 readiness 的等同：状态机设计只有在真实产线/OTA/现场验收语境时进入本 Skill。不要堆 Python/Web/数据库语言黑名单，也不要新增领域 Skill。

- 正：明确嵌入式量产、产测、现场诊断准备、设备 OTA/恢复验收仍选择 production Skill。
- 正：Python/普通 Web 异常诊断选择 systematic-debugging；措辞不确定时 abstain，不猜硬件。
- 反：DB rollback、纯设备状态机设计、模拟器学习不进入 production readiness。
- 反：“只读评估现场 OTA 回滚，不执行刷写”保留正确 Skill，mutation 仍 deny；否定量产/OTA 的请求不被相邻主题强行抢占。
- 保留：实际设备 owner、来源/型号、授权、现场证据和 ready 签署要求不放宽。

## 未并入四项实施的观察与排除

### O-01：ADR 写作动作与接口兼容主题碰撞

实际输入“请写 ADR，记录我们已经接受的 API 接口兼容方案”选择 `adk-component-api-stability`，而非 `adk-adr-writer`。`manifest.json:2663` 已有 `写ADR/架构决策记录/ADR`；`_matcher_kernel.py:569-576` 按命中词 specificity 选取，主题可能压过明确文档动作。此 observation 保留在 `routing.json:adr-operation`。本组四项先修范围不包含通用多意图优先级改造；若单独修，须同时检验“依据现有 ADR 评估接口兼容”仍选择兼容分析，不能把每个 ADR 提及都改成写作。

### O-02：cross-team 是刻意的 supporting explicit-only

“请为跨团队交接生成一页说明”在 auto scope 返回 `supporting-skill-explicit-only`。`manifests/skill_content_contracts_v2.json` 明确设定 supporting/explicit-only，`matcher.py:380-390` 按此执行；显式选该 Skill 的正例仍通过，原生导出 skill_invocation 也保持 Manifest 所声明的 implicit。这暴露 ADK source matcher 与用户自然任务入口的产品选择问题，但不是实现违反当前合同，不能擅自升级为 primary 或改权限。单列待 owner 决定，不混入 W-03/W-04。

### 排除：human approval 与独立 AI 委派

`adk-after-action-review/SKILL.md:51` 要求正式规则晋级/高风险持久写入的 human approval；`docs/agent-operating-rules.md:148-154` 允许已授权范围内的独立 AI 作 Spec/Quality 最终裁决。两者分别约束资产晋级/外部效果与审查职责；`manifests/agent_improvement_loop_contracts.json:104` 也保留 before-apply human approval。没有证据表明委派记录覆盖了某次实际 guidance promotion，也不能据此要求重复向用户确认。此候选为 **not-established / 不实施**。

### 排除：所有源码根引用都等于导出缺依赖

AAR 的三份本地 templates 已随 reference 导出，且与 canonical 模板逐字节一致；artifact-gating 的 llm_agent helper 是受限条件入口；pilot 的源仓评测文档是条件性来源。不是所有 source-relative 路径都构成使用阻塞。W-01 只针对 machine-v2 必需合同既缺自包含定义又与真实 validator 不一致的具体路径。

### 不作为已证缺陷的潜在边界

- Draft PR/PR-only CI 的先后问题缺目标项目必需 CI 契约，不靠通用推测改分支门禁。
- verification checker 示例明言非生产 Gate，其演示范围不等于完整安全解析器；不凭可新增更多检查就认定当前范例错误。
- API ABI、离线 GDB、真实 Pilot、现场 readiness 和多轮设计探索均没有相应输入/运行条件，本次只报告已查范围，保留 not-run。

## 最小实施包建议

| 包 | 改动范围 | 必需验证 | 保留边界 |
|---|---|---|---|
| W-01 | task-breakdown 正文/reference 的 payload/envelope 区分；提取实际随包样例的回归 | 两 target 导出样例 → 原 validator；未知字段/错误权限/错误 gate/prototype 缺证据反例 | 不扩大 v2字段、不增加 schema 版本、不把方法说明当授权 |
| W-02 | `intent_boundary.py` 的任务字段类型防护；独立 contract 回归 | 四 malformed fixture 与合法四 work-item kind、原拒绝路径 | 不 coercion、不 catch-all、不放宽权限 |
| W-03 | review/commit 的现有 trigger 与 manifest intent；auto routing 回归 | 中文同义词、反馈、commit control、否定控制 | mode/权限与真正 review/readiness 分工不变 |
| W-04 | production/systematic debugging 触发边界；已有领域条件/manifest route；auto routing 回归 | 明确现场正例、通用诊断、DB/纯设计反例、只读/否定控制 | 设备/发布授权和 evidence requirements 不放宽 |

优先替换含糊原句与错误 trigger，不增加长默认模板。已有 profile context ratchet 不应放宽；最终预算由父 Agent 在合并改动后的真实 source footprint 复测。本报告不估算 Token/耗时收益。
