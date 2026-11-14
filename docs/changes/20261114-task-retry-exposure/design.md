# 设计

`adk-task-events/v1` 中每条加载事件保持唯一 event_id 和连续 seq。导入器的 `ledger.skills` 是运行级暴露投影，不是原始事件账本；因此可以在确认同名事件的摘要和 primary 角色一致后，仅在该投影保留一条身份。

每条事件仍先经过已有封闭字段、布尔类型、摘要、身份和顺序校验。已有同名暴露相同则不重复追加投影；不同则 fail closed。不会忽略冲突事件，也不会改变 attempt、模型 call、工具、handoff、验收或配对分组。原始账本通过 events_ref 保留字节绑定。

同名过程 guardrail 的运行级状态按 `failed > passed > not-applicable` 聚合一次，并保留支持该状态的实际证据引用；全部原始事件和引用仍逐条核验并由原始账本绑定。报告中的 guardrail 和 verification 名称维持既有 `process/<name>`，单次事件输出不变；后续 passed 永不覆盖此前 failed。不得仅验证被选中的证据，也不引入另一套事件身份或虚构计量。

公共 observation schema 和输出字段不变。全库检索已覆盖 `skill-load`、`ledger.skills`、`import_task_evidence` 与 task trial 调用；本次不增加动态导入或反射入口。只对之前误拒绝的有效重试输入增加兼容接受路径。

共享导入逻辑按标准完整门禁执行。设计/协调/发布由 ai/root 负责，实现和独立只读审查分别委派。回退为撤回修复版本并恢复既有单次暴露限制，不改历史观测或历史发布资产。
