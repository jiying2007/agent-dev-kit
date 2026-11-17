# Skill usability 独立 Spec / Quality 审查

## 当前裁决

- 审查角色：新 reviewer，只读；没有参与本轮实现、修改仓库、提交、push、联网模型执行或 live runtime 操作。
- 比较基线：`78c3be7f6f9b5ee2e557de54156532fb3169198d`（11.3.13）。本次初审对象为协调者冻结的候选工作树；最终 commit/tree 绑定待协调者提供后补充，当前 HEAD 仍为基线，不能以 HEAD 代替候选源码身份。
- **Spec：needs-fix。Quality：needs-fix。** 当前确认两个 P2 正向路由回归。均未观察到写权限提升；问题是已适用任务的新拒绝路径。
- 此报告不构成组件发布、Root 消费、原生 runtime 或设备资格通过证明；这些仍需其各自实际证据。

## F-01 / P2：领域门槛误拒绝原本有效的 OTA readiness 请求

位置：`skills/adk-production-field-readiness/SKILL.md` 的 `implicit_context`（初审第 19 行）。该 Skill 仍声明 `OTA` trigger，但新增上下文仅接纳 `OTA升级/OTA回滚/OTA验收` 等相邻短语。

真实生产 matcher 对以下三个输入的基线/候选结果：

| 输入 | 精确基线 | 候选 |
|---|---|---|
| 评估嵌入式设备 OTA 的断电恢复、回滚和上线 readiness | `adk-production-field-readiness` / routing | `needs-triage` / `match=false` |
| 请只读检查 OTA 签名和回滚验证证据 | `adk-production-field-readiness` / routing | `needs-triage` / `match=false` |
| Review OTA firmware rollback readiness | `adk-production-field-readiness` / skill_trigger | `needs-triage` / `match=false` |

三个任务均具有明确 OTA 领域，且属于正文的签名、断电恢复或回滚证据检查；不是用普通数据库回滚偷渡设备上下文。基线与候选的 matcher/kernel 文件字节完全相同，差异由真实 Manifest/Skill 数据驱动。候选没有接纳存在但非相邻后缀的 OTA 提示，违反 U02 对真实 OTA 和原适用正例的保留要求。

原始证据：`review-probes.json` 的 `routing[0:3]`；独立脚本从 Git archive 精确提取基线资产，不改工作树。三个结果的 `mutation_permission` 始终为 `deny`。

最小修复 task：使肯定的 OTA 域提示继续满足现有上下文检查；保留纯数据库回滚、引用示例 OTA、否定 OTA 的拒绝路径，不引入新分类器或权限来源。将上述非相邻中文和英文正例加入真实 auto matcher 回归，不能只测试恰好含 `OTA回滚` 的输入。

## F-02 / P2：新增 RTOS 名称门槛拒绝已适用的 VxWorks 任务

位置：`skills/adk-rtos-task-design/SKILL.md` 的 `implicit_context`（初审第 11 行）。新门槛只接受 `RTOS/Zephyr/ThreadX/RT-Thread`。

复现输入：`请为 VxWorks 做任务设计`。

- 精确基线：`match=true`、`skill=adk-rtos-task-design`、`source=skill_trigger`。
- 候选：`match=false`、`reason=needs-triage`。
- 对照 `请设计 FreeRTOS 任务优先级` 和 `请为 Zephyr 做任务设计` 两版本仍可匹配；`裸机系统没有 RTOS；请评估实时任务设计` 在候选正确退出。

这不是一个从未支持过的泛化同义词请求，而是 `任务设计` 现有触发在新增领域门槛下的正向回归；任务明确给出 RTOS 产品名称。U06 要求保留真实 RTOS 上下文，因此应修复这个已复现的最小缺口，或明确记录为接受的范围限制；不能同时宣称原适用正例无回归。

原始证据：`review-probes.json` 的 `routing[8]`。权限保持 `deny`，没有 runtime 或设备动作。

最小修复 task：在既有 `implicit_context` 中保留这条明确领域输入，并加真实 auto matcher 对照；继续保留销售团队任务设计、明确无 RTOS、引用和否定域提示的拒绝路径。无需穷举所有平台或扩成自然语言分类器。

## 已核验且没有新增阻断的部分

| 验收 / 边界 | 实际核验与判断 |
|---|---|
| 65 项审查记录 | `groups.json` 的 20+25+20 个身份互斥，65 项合集精确等于当前 Manifest 的 56 core + 9 optional；`audit-index.json` 的 34 个归档证据均存在且 SHA-256 匹配。逐项判断来自三组原始报告；本终审没有冒称重新全文阅读所有 65 个 Skill。 |
| U01 review 归属 | 阅读真实 intent/frontmatter 变更并调用 matcher；“只读核验本地修改的代码评审结果”从 commit gate 改为 review-loop；“不要做代码评审，只发起PR”保留 commit gate，均 deny。 |
| U03 canonical 包 | 19 字段集合与 `structured_output_contracts.json` 字节未变；读取发布 JSON、类型/枚举/权限表和 scope 映射，实际导出示例通过真实 validator；额外顶层字段依然拒绝。 |
| U04 类型错误 | 独立基线对照复现 `artifacts=null/[1]`、`work_item_kind=[]`、`retention_decision=[]` 的原异常；候选均返回错误 tuple。进一步对 task 全 19 字段、四个 work kind、prototype 全 16 字段和根值共 1,410 个 JSON 值扰动，没有异常或非 tuple 返回。该矩阵检查异常边界，不将所有类型正确的替换都视为应拒绝。 |
| prototype 相邻边界 | 新 guard 在 retention 和 expiry 上先验证类型；无宽泛 catch、无将非法值转成合法字符串。任务 permission/exit gate 和 prototype evidence 必需条件仍存在。 |
| U05 RTA | 公式的适用前提明确改为每任务固定且互异的优先级；同级另选模型。两任务各 C=6、D=10 的共同窗口需求为 12>10，不会因每项只看严格高优先级而宣称可调度。新测试只为主机算术及方法适用性，没有冒称 RTOS/HIL 测量。 |
| U07 / U08 | 真实 matcher 验证 BSP 梳理正例、域外 BSP 否定对照、DMA CPU budget 正例和无 IRQ/DMA 的轮询反例。没有改 matcher 的授权计算。 |
| U09 导出依赖 | 阅读两个 optional 的命令前提、真实 compiler 导出检查和 catalog 实际调用测试；helper 缺失时明确目标已有入口、not-run、不安装与不伪报。core/optional 两查询保留嵌套 optional 的完整身份。 |
| U10 archive | 只读 metadata 与 matcher 权限保持；正文明确 candidate task → 既有已授权实施 owner → 实施回执复核。旧 hash / 实测 hash / 可信原件 / 未知 needs-fix 的条件均保留，handoff 不是新授权源。 |
| parallel / planning 映射 | 阅读人类信封及逐字段映射：scope_read/scope_write/must_not_touch/global_constraints/interfaces 进入 constraints，身份/owner/report/noise 等进 context 或外层；ready 条件与实际状态分开。实际映射回归通过 validator，范围没有因移除顶层键而消失。 |
| 身份和权限 | 65 个 `(section,name,path)` 与精确基线相同；65 项 `resolve_skill_content` 元数据均相同。没有新增权限 ceiling、optional 隐式安装、runtime、设备或发布资格。 |
| 8 ratchet | ratchet 文件与精确基线字节相同；独立调用生产 `enforce_profile_ratchet`，8 项均 pass，未提高阈值。初审最紧为 large-refactor full source 323298 / 323328。仅源字节，不是 Token/模型成本测量。 |

## 测试质量判断

新增 validator 测试覆盖真实旧错误路径，并保留所有 work kind 的合法和错误 permission/exit 对照；导出测试消费 compiler 实际交付的 JSON，再交真实 validator，具有超出关键词检查的价值。catalog 测试运行发布命令并检查全集身份；parallel 映射用 sentinel 追踪字段，避免只靠相同字段名宣称 scope 已保留。

optional fallback、archive 交接和部分 RTA 前提的测试仍包含文字标记断言。对纯方法资产，这是结构保护，不能单独证明模型遵从或实际交接成功；本终审已人工核语义，仍将真实模型/宿主执行列为未验证。新增路由回归测试未覆盖 F-01 的非相邻 OTA 及 F-02 的明确 RTOS 产品名，所以新增测试全通过本身不能推翻这两个真实失败。

本 reviewer 只运行定向验证，没有重复协调者正在执行的 102 suite。最终定向日志和整合证据将在修复后的精确源码绑定阶段登记。

## 实际读过和执行过的范围

已读：根 `AGENTS.md`、`docs/agent-operating-rules.md`、根 README、当前 change 的 requirements/design/tasks/negative-results；相对基线的全部已跟踪差异；新增两份 consumer/task-package 测试；完整 `intent_boundary.py`、公开 matcher、相关 kernel 的触发/否定/上下文/路由路径；profile footprint 与 ratchet owner；task-breakdown、parallel、planning、archive、两个 optional 的变更正文与相关完整交接内容；三组 baseline 审查报告及其覆盖/证据索引。大型原始测试日志没有逐行重读；原始工件完整性通过摘要验证。

已执行：真实基线/候选 matcher 对照 16 条；真实基线/候选 validator 四个原错误对照；1,410 个 JSON 值扰动；65 身份/权限元数据比较；canonical schema 与 ratchet 字节比较；8 个 profile 生产 ratchet；34 个 baseline evidence 摘要与 65 项互斥覆盖比较；定向 consumer、task-package、RTOS 和 trigger 测试。

审查自身负结果：一次探索性文件搜索使用了不存在的 `src/agent_dev_kit/trigger*` / `tests/test_profile_context_ratchets.py` 路径，返回 exit 2，随后定位到 `_matcher_kernel.py` 和 `test_profile_context_footprint.py`；一次只读覆盖摘要脚本括号错误返回 SyntaxError，修正后返回 34 个摘要一致、65 项精确覆盖。均不计作产品缺陷。

未验证：native Skill discovery/load、真实 LLM 消费、原生 dispatcher、真实权限 enforcement、生产续行/去重、外部服务、模型 A/B、provider Token/时延/费用、设备/现场结果、main CI、不可变 Release、Root 两路径消费。原生效果与资格不能由本报告静态通过继承。

## 最终绑定（待补）

最终 source commit/tree、F-01/F-02 处置、修复后定向回归、协调者整合日志与最终 Spec/Quality 裁决在此处追加；保留本次初审负结果，不覆盖原始回归证据。

## 修复后复查记录

本节记录初审后的处置；上方两个 needs-fix 裁决及原始 `review-probes.json` 保留为初审时点的负结果。最终提交与完整回归尚未绑定，因此此处只给出修复复查结果。

- **F-01：fixed。** 实现者恢复肯定的 `OTA` 领域提示；三个初审失败输入均重新选择 `adk-production-field-readiness`，read-only ceiling 和 `mutation_permission=deny` 保持。
- **F-02：fixed。** 实现者仅补入已复现的 `VxWorks` 域词，正例恢复 RTOS Skill；销售、明确否定或无 RTOS 的边界仍拒绝。
- F-01 的修复另需要紧凑并列否定处理。已阅读并核对追加的设计，以及 `_has_affirmative_context` 全部实现：只跨当前 Skill 已声明域词间的 `或/和/与/及/、/and/or/nor` 继承首项否定；中间新动作、逗号、句号、分号等不属于这些连接串，因而打断继承。调用只在 `_implicit_context_matches` 内替换 eligibility 检查。全局 `_is_locally_negated`、action/mode 分类和权限计算没有改动。
- 独立预选的 17 条输入覆盖紧凑多项否定、新句和逗号/分号、重新肯定同名域、`而是` 转折、英文 `not/without`、引用例、合法 inline code、RTOS/VxWorks 正反例，全部满足期望且 deny。原始输入与完整结果见 `postfix-probes.json -> independent_regression_cases`。
- 独立运行四个定向模块共 **39 tests，全部通过，0 failure/error**。原始 stdout/stderr 在 `postfix-targeted.log`，argv、退出码 0 和耗时在 `postfix-targeted.json`；可重放入口 `run-targeted.py`。不是协调者 102 suite 的替代品。
- 修复后再次核验 65 身份、全部权限 metadata、原 canonical schema/ratchet 字节，以及八个生产 ratchet，均通过；再次执行 1,410 个类型扰动，异常与非 tuple 结果仍为零。
- `.gitattributes` 新增 8 个精确 evidence 路径的 `-whitespace`，目标是保留原始 diff/失败输出；没有通配放宽源码检查。其是否随最终 commit 保留仍需最终绑定。
- `postfix-probes.json` 包含本次读取的变更文件 SHA-256。因为这轮额外改动了 kernel，复查脚本现在在隔离目录中执行**基线自己的 Python 包和资产**，不再将候选 kernel 用作旧基线代理；此前初审的 kernel 字节相同证据和旧负结果仍保留。

修复后当前工作树未发现其他阻断 finding。已解决 finding 不免除整合测试、最终源码绑定或发布/Root 证据要求。短语 matcher 的适用范围仍是声明域词与有限否定语法，本审查没有将它认证为任意自然语言分类器。

## 最后 helper 冻结与整合证据复核

- 最后 helper SHA-256：`3b4364f90f7f0858e66f937a7e1b3c00c5afe19da3dd9a2c1ab542b6d420ca60`。实现将遍历全部 `negated_ends` 改为固定 8 个连接词的反查：`position-len(conjunction)` 必须是一个已知否定结尾，且对应子串等于连接词。该存在条件与原实现等价；所有保存的结尾非负，因此较短位置不会因 Python 负下标误命中。匹配排序、极性 owner 和权限路径未改。
- 对这次等价改写只重跑 17 条独立路由边界，全部通过；没有重复运行无关 39 项。结果与逐条完整返回在 `linear-helper-probes.json`。相对 `postfix-probes.json` 的代码变化只有 kernel；另外两个变化是 CHANGELOG 补入已修范围，以及 `.gitattributes` 新增两条 review-fix 原始证据路径，后者累计为 10 条精确路径，仍未放宽源码检查。
- 协调者最终 `tested-source-files.json` 包含 650 个文件摘要，独立逐一计算当前字节，全部匹配。此时完整 102 suite 仍在执行，未提前记为全量通过。
- 9 项质量/合同检查的退出码均为 0，且独立核对每份实际日志 SHA-256 与 `quality-results.json` 一致：strict、format、module-size、Ruff、focused Ruff、mypy、pip-audit、release check、target static。
- 独立核对两个实际导出的各 119 个文件：每目标 65 个 Skill entry、54 个 support 文件，全部与 export inventory 摘要相符；54 个 support 的实际字节逐一等于源路径。两个 inventory 摘要分别为 Claude Code `29a21b58282ff1564d5051ce2f41c64332651c6c2856d00e3f9bb834eb86fb52`、OpenCode `c9ff47982e2710b3456c52f04433302a48d32384079a2dee30f9dfa4e4395751`。记录在 `final-evidence-integrity.json`。
- 已读 exporter 的 `_render_support_files` 和 `export-verifier-negative.json`：34 个 README/LICENSE/UI metadata 不在既有 target `support_directories` 范围。协调者最初验收脚本把这些文件算入应分发集属于验证器范围错误；已保留原失败并按未改的生产合同修正，没有为通过测试删除必需 support 或修改生产导出边界。

以上仍是源码/静态导出与本地验证证据；最终 source commit/tree 和完整回归结束状态待追加。

## F-03 / P2：全量回归发现泛诊断意图抢占真实 SSH 调试任务

发现来源：协调者的完整 102 suite 首次结束为 **101 PASS / 1 FAIL**，失败 owner 为 `test_software_m5_ready`。本 reviewer 随后独立调用生产 matcher 复现；不能将这个整合失败归为通过，也不能修改 fixture 的 expected 来规避。

- 固定 fixture：`tests/fixtures/software_m5_eval_tasks.jsonl` 的 `route-054`。
- 原始输入：`立即进行 SSH调试：登录生产设备，抓取日志并执行诊断命令。`
- 原 expected：`adk-embedded-debug-transport`；候选实际：`adk-systematic-debugging`、`source=routing`。
- 根因：新增的全局 `systematic_debugging` intent 同时得到了“调试”和泛“诊断”的 specificity，抢过已有专用 SSH routing；这与把普通诊断交给通用 Skill 的目标不同。
- 独立原始返回与该时点 raw Manifest SHA-256 `f5703ddff0c58822e5e452092d4497eb9ab19d36033108b0fcdaac78ecee906c` 保存在 `ssh-regression-before.json`。
- 权限仍为 `deny`；软件路由评测明确 `safety_evaluated=false`。此 finding 是路由所有权回归，没有观测 live SSH、设备写入或权限绕过。

相邻控制：`只读 SSH调试：检查连接并诊断设备日志。` 当前选择 `adk-embedded-remote-debug-log-triage`，这是更具体的设备日志 owner；修复不能把所有包含 SSH 的任务强行归 transport。普通 Python 诊断与现场诊断 readiness 的原始对照也保存在同一 JSON。

最小修复 task：保留专用 routing 的优先意义，把泛诊断放到既有通用 Skill 的适当 fallback 入口或其他等价的最小既有机制；维持 Python/Web/普通命令诊断正例、SSH 与日志相邻 owner、否定意图及原权限。原 `route-054` expected 不动，并重新执行实际 route corpus 与所需完整回归。

该时点 **Spec / Quality 重新置为 needs-fix**；前两项已修与其证据继续有效，但上一轮 650 文件快照及质量/导出记录不能自动当作下一次源码修改后的最终验证。完整失败原件位于协调者的 `skill-usability-validation-final/full-regression-result.json` / `full-regression.log`，退出码 1，原始 log SHA-256 为 `cd235c737f138d433cc0f95fadbd78eafa354d222ae75b8c430e554acdf26b0c`。

## F-03 修复后复查

**F-03：fixed，最终完整回归和 source commit 仍待绑定。** 已核最小 diff：撤回 Manifest 的本轮泛 `诊断` 路由词，将既有 systematic Skill trigger 从 `诊断循环` 缩为 `诊断`（局部版本 1.2.6），不再修改 matcher。原有 `诊断循环` 仍被新 trigger 覆盖。

独立预选 13 条真实任务输入全部满足 owner 与 deny 预期，包括原 `route-054`、设备日志 owner、Python/Web/普通命令、禁止诊断、已有根因无需再诊断、明确 commit/review/ADR 的相邻任务、现场诊断与 OTA。实际原始结果见 `ssh-regression-after.json`，重放脚本 `followup-routing.py`；其中 raw Manifest SHA-256 为 `90d87a3e4aef91b649d053b18b4ac87f65ed28ded61ae51fdc021eea5a8ca77b`，systematic entry 为 `1b14158259d16fa98b93212fd719ac92e1da37d03ae055faedb48d7b7a3c9c45`，kernel 仍为 `3b4364f90f7f0858e66f937a7e1b3c00c5afe19da3dd9a2c1ab542b6d420ca60`。

泛诊断现在通过既有 `skill_trigger` fallback 选择 systematic，普通输入保守为 `needs-triage + deny`，显式只读输入为 `readonly + deny`。U02 要求正确通用 owner 并保留权限边界，没有要求把所有诊断语句升级为命令执行模式；因此该行为满足本项验收。选择 Skill 不构成执行命令、写文件或操作设备的授权。

新增测试直接读取既有 `route-054` 的原 prompt，并断言其 expected 仍为 transport，另覆盖 ADB、串口、日志 owner、泛诊断和否定控制，具有实际防回归价值。当前源码没有未解决的阻断 finding；先前 101/102 失败记录保持原样，修后需新的完整套件结束证据。

## 最终 source-change 裁决：Spec pass / Quality pass

本节是上述初审、修复复查和再次发现回归之后的最终裁决；前文的 needs-fix、待定状态和负结果是各自时点的真实记录，全部保留。

**Spec：pass。Quality：pass。没有未解决的 blocker 或 major finding。** 三个 P2 finding 均为 fixed，最终评审绑定以下精确源码，不能自动延伸到后续包装、合并、发布或 Root 消费。

| 身份 | 绑定值 |
| --- | --- |
| Base commit | `78c3be7f6f9b5ee2e557de54156532fb3169198d` |
| Reviewed source commit | `a2b90b64d3ba83ac0c856ddb6a541450ead1bd36` |
| Source tree | `53534d897a42e816525e310aa28134751ca5783f` |
| Original patch SHA-256 | `21dcecb8567e84e0bf3818185f3281827812d8d65dcf73a213e394578aeac414` |
| 最后独立证据完整性核验 | `2026-11-17T07:06:01.106886+00:00` |

审查人用 Git 对象重新生成 base→head 的原始 diff，1,892,765 bytes 与仓内 `evidence/original.patch` **逐字节相同**；没有仅依赖协调者填写的 commit 名称。191 个变更路径的 blob ID、字节数和 SHA-256 全部与 `evidence/source-bindings.json` 相符，最终套件的 650 个被测输入摘要全部与该提交中的 blob 相符。此时当前工作树相对这份被测输入清单只有 `.gitattributes` 的后续包装变化；`tasks.md` 的后续状态更新也不属于本次源码裁决。两个文件的原始源码版本已保存在原 patch，后续包装须单独做增量审查。

### 最终 finding disposition

| Finding | 严重度 | 最终处置及证据 |
| --- | --- | --- |
| F-01 OTA 正向路由回归 | P2 / major | fixed。恢复肯定 OTA 域词；原三条不相邻后缀的中文/英文正例恢复正确 owner，否定、引用、普通数据库和新动作边界保留。最终 helper 的 17 条独立输入全部通过。 |
| F-02 VxWorks 正向路由回归 | P2 / major | fixed。既有 RTOS 上下文仅补充已复现的 VxWorks；肯定任务恢复匹配，域外/明确否定仍退出；权限不变。 |
| F-03 泛诊断抢占 SSH route-054 | P2 / major | fixed。撤回全局泛诊断 routing 新词，使用既有 systematic Skill trigger fallback。原 fixture expected 不改；13 条独立 owner/否定/只读对照全部通过，最终完整套件中的 `test_software_m5_ready` 通过。 |

Skill 选中与执行授权保持分离：普通泛诊断仍可为 `needs-triage + deny`，显式只读为 `readonly + deny`。所审最小 helper 仅改变 `implicit_context` 的紧凑域词并列否定资格判断，没有改变 action、mode、permission 的极性 owner，也没有通过测试 fixture 更改掩盖专用路由回归。

### 最终整合证据与复用边界

- 完整回归由协调者在最终冻结源码上执行，本 reviewer 独立核对原始日志、退出码、timing 和输入快照：**102/102 suites PASS，exit 0，343.573 s**；结束于 `2026-11-17T07:02:47.745648+00:00`。日志中有 102 个互异 PASS owner，名称集合与 timing 完全相同，没有 FAIL 行。原始日志 SHA-256 为 `0d1bee4e82001511f12291d9c3be0867228a5a396f58b49d3acd176ef3eed61e`。
- 这不是把第一次完整回归的 101/102 失败改为通过：原失败结果与日志留在 `evidence/first-full-run/`，更早的主动停止 exit 130 留在 `evidence/pre-review/`。新的通过记录在 `evidence/final/`，28 份最终/修复工件均与 `final-evidence-index.json` 摘要一致。
- 最终质量检查中 **strict、format、release-check、target-static 四项重跑**；**module-size、Ruff、focused Ruff、mypy、pip-audit 五项复用**上一轮已通过且输入未变的结果。九份实际日志的摘要均核实。旧、新 650 文件快照仅 `manifest.json`、`skills/adk-systematic-debugging/SKILL.md`、`tests/test_skill_trigger_matrix.py` 三个路径不同；`src/` 和依赖声明摘要不变，五份复用日志逐字节等于原件。快照没有收录 `tools/`，该目录无本轮源码 diff，不能声称已对其做前后快照字节比对。不能把五项复用写成重新执行，也不宣称后来再次查询了漏洞数据库。
- 两个真实导出分别是 **65 个 Skill entry + 54 个支持文件 = 119 个文件**。我逐项核对实际导出与 inventory 的摘要，并逐项核对 54 个支持文件与源字节。最终 inventory SHA-256：Claude Code `84f4fd3474576492e00ebe45e98e5418347c21e143c48dd00a24abbeb23c6902`；OpenCode `819ff88c80d9a67adba8bfcc24e637a6461843a88fb46bbff2728f0d76507d7a`。这证明约定分发集合与独立交付内容一致，不证明原生宿主发现/加载成功。
- 65 身份和原权限元数据比较保持通过；canonical schema 与 ratchet 阈值未改。最终 8 个 ratchet 均通过，最紧的 large-refactor potential full source 为 **323,274 / 323,328 bytes，余量 54 bytes**。余量很小是后续增长限制，不是当前超限；没有把源字节当作 Token 或运行时上下文测量。
- 我此前独立执行的 39 个定向测试属于 F-01/F-02 修复阶段，未伪称全部重跑在最终提交上。最终线性 helper 的 17 条输入与 F-03 修复后的 13 条输入均已通过，相关最终文件 SHA 与 `a2b90b6` 精确一致；102 suite 提供最后整合覆盖。

### 合同与使用自洽性结论

U01–U10 在此次源码范围内满足已登记的可观察条件。生产 validator 的真实旧错误路径被类型 guard 收束为错误 tuple；合法 work kind、权限拒绝及 exit gate 控制保留，没有放宽 schema、吞掉未知字段或把非法值强行转成字符串。1,410 个扰动验证的是已解析 JSON 值进入 validator 后的异常边界；原始 JSON 文本解析和任意恶意语言解释不在该覆盖声明中。

导出 task-breakdown 的 19 字段机器包与 parallel/planning 的人类信封分开说明；scope、接口、全局约束、owner/report 信息仍有合法承载位置，未因清理额外顶层字段丢弃。optional helper 明确只适用于已核 ADK 源根；纯导出环境使用目标既有入口，未运行步骤保持 not-run/unavailable。archive 的只读定位、候选修复和已有授权 owner 交接保留效应边界。以上结论既依据真实导出和工具调用，也包含对正文语义的逐段阅读，未用关键词测试代替所有行为验证。

最终补读开发消费观察及其新机器包，并再次通过当前生产 validator 验证两份原始产物：旧包仍为缺 15 / 多 11 字段，新包返回空错误 tuple。新包保留两个只读路径、空 write scope、禁止网络/设备/实施、真实未解决 blockers 及 `implementation_permission=forbidden`；“通过 schema”没有被写成已经执行研究或可直接调度。两次任务 wording 与上下文不同，不能作为注册配对 A/B、因果效果、Token/费用/延迟收益或原生 runtime 资格。这里是留存产物的开发消费观察，审查人没有另外启动模型任务。

### 最终覆盖及未验证边界

本轮独立审查覆盖全部变更 diff、实际 owner 路由、声明域词否定的局部边界、validator 错误路径、导出自洽性、scope/权限映射、身份/ratchet 约束、测试价值和最终证据链。未冒称重新全文审查所有 65 个原 Skill，也未逐行重读所有历史测试输出；65 项覆盖和原始材料完整性通过逐项记录、互斥身份集合及摘要验证。

以下仍不由本次 source-change pass 证明：native Skill discovery/load、原生 dispatcher 与权限 enforcement、生产续行/去重、真实 SSH/设备/RTOS/HIL 或现场运行、注册模型 A/B、provider usage、main CI 的实际运行、不可变组件 Release、Root 两路径消费及产品/设备资格。需求中的这些后续交付义务没有被取消，也没有在本报告中登记为完成。本 reviewer 未修改产品仓库、提交、push 或执行 live runtime；审查报告与验证脚本只写入指定 reviewer 目录。

最终机器可读核验结果写入 `independent-review.json`；原始定向输入/输出保存在 `evidence/independent-probes/`。canonical `adk-review-evidence/v1` 记录绑定此报告、原 patch、精确 source 与最终证据，待协调者原样复制后由真实 validator 核验。
