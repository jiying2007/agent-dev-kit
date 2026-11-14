# 11.3.0 独立源码审查

本记录归档独立只读审查者 `ai/root/review_existing_candidate` 的实际结论，由协调者保存。
实现者为 `ai/root/implement_task_evidence`、`ai/root/implement_skill_workflows`，协调/设计/发布为 `ai/root`。
审查者没有写实现、测试或文档，没有提交 GitHub 评论、review 或 approval。
AI 身份为过程声明，不是平台认证或人工审核。

## 来源

- Base：`ebef1106aeecbe14e9ac676b2950b81895c1ea5b`。
- 审查源码：`c1ccff024b70155515dc002cf222dd6edb986363`。
- Source tree：`a4b983f63acb038c7fe9966a29fb9c05d8e82df8`。
- 完整差异与75个文件的来源摘要在 `evidence/original.patch`、`evidence/source-bindings.json`。
- 本审查材料是随后单独保存的元数据，不把它自己的提交当作原被审查源码。

## Spec / Quality

**Spec pass；Quality pass；open blocker=0，open major=0。**
独立审查覆盖三个非执行CLI、三个typed业务模块、22项导入与15项配对测试、12项产物验收测试，
实际runner与CI类型检查接入、36个开发任务文件、六处已有方法差异、版本投影、预注册历史和运行说明。
最后额外核对MCU引用精简、grader/importer路径协议一致性，以及已发布Git对象与原冻结摘要一致。

任务成功由不同于executor的声明grader和真实可读取产物验收产生，不由路由命中产生。
完整事件账本保留失败/重试/子任务用量；缺测或估算不补0。过程guardrail不能被最终产物通过掩盖。
任务预算timeout与未加载保留在分配人群；不同初始状态、控制污染和错误版本另标无效。
配对入口逐任务核对实际绑定后复用原统计器，不修改既有RunEvidence、路由materializer或统计语义。
`source_sha` 是任务初始仓库commit；ADK干预版本依靠固定bundle、Skill内容与原发布材料区分。

## 发现闭环

| ID | 级别 | 状态及依据 |
|---|---|---|
| task-evidence-output-overwrite | major | fixed：完整read-set与既有atomic_io拒绝覆盖输入及软硬链接；invalid不落盘；有真实CLI负例 |
| task-evidence-unchecked-pairing | major | fixed：独立纯内存反例确认原通用入口缺口；新入口把输入/workspace/source/分组/grader/provenance绑定到dataset_ref，逐观察核对后比较 |
| development-fixture-ignored-log | minor | fixed：build.log被ignore，改为build-output.txt并核对全部36个fixture可收录 |
| profile-source-budget-growth | major | fixed：只精简MCU引用至1529字节，profile为46580、原上限46612；未提高预算；定向6/6复验 |
| grader-importer-path-drift | minor | fixed：复用EVIDENCE_PATH_PATTERN并补空格/冒号负例；最终源码及测试摘要重新审阅 |
| runbook-schema-field | minor | fixed：补充封闭输入的schema_version；不把导入报告的authority字段混入acceptance |

## 验证与时间

原T2冻结审查为2026-11-14T12:26:32Z至12:27:20Z，T3冻结复核为12:25:35Z至12:27:20Z。
最终内容增量复核为12:28:41Z至12:32:17Z；随后按真实Git提交重新核对来源与新增验证材料，
该次时间在typed record与绑定观察中单独记录，不改写此前时间。

实现者报告41项RunEvidence入口测试、12项开发工件测试、71项content、14项trigger及相应预算/类型检查通过。
协调者执行strict validation、版本校验、格式检查、最终profile 6/6与四模块strict mypy/Ruff通过。
首轮完整集成诊断是**101/102**，唯一profile失败已修复并定向复验；保留原始失败日志，
没有把该轮写成102/102。最终PR/main完整CI和不可变Release必须独立核验。

## 限制与未完成实测

所有源码审查、开发case及合成比较仍是caller-observed/test-only，不能认证历史宿主、记录完整性或grader身份。
静态工件检查只证明所规定格式和文本范围，不覆盖所有等价程序，不执行候选代码或任意命令。
没有Codex/ChatGPT Work、付费模型、设备或新调度执行；E2–E4、真实任务完成率、Token、费用与时延未测。
未知真实记录保持evidence-blocked，恢复入口为 `docs/runbooks/task-evidence.md`。
既有change没有持久化lifecycle stage，本记录不伪造状态转换，也不产生release或产品资格。
