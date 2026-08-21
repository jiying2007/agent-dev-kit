# Design

## Role separation

- 外部 diff reviewer：固定输入快照，扩大语义风险扫描覆盖面，输出结构化候选 finding。
- 本地 review loop：使用需求、完整源码和测试证据核验 finding，管理修复与复审闭环。
- verification gate：执行确定性的构建、测试、格式和资产一致性检查，不替代语义审查。

## Snapshot contract

每轮审查声明目标 `staged | working-tree | whole-branch`，并记录 HEAD 与 index/diff 指纹。staged 文件存在 unstaged overlay 时，旧快照只覆盖 index；修复必须重新 stage 并生成新身份后才能计入复审。

## Independence contract

报告区分 `independent` 和 `author-self-review`。自审仍有价值，但高风险或共享逻辑不能把自审写成独立审查证据。

## Compatibility

本次只扩充 Markdown 输出契约，不改变运行时 API。旧消费者可忽略新增字段。
