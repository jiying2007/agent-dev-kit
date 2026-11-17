# 只读 research handoff 说明

## 本次完成的工作与状态

已准备 `task-package.json`，采用指定 Skill 的机器分发 v2 格式，保留其 19 个顶层字段。`work_item_kind=research`、`implementation_permission=forbidden`、`exit_gate=evidence-reviewed`；`strict_schema_decision=true` 表示严格遵守合同的要求，不表示接收方已验证成功。`refusal_handling` 保留为 `blocked or replan`。

本次只准备交接，没有研究 decoder、执行测试、访问网络、删除文件或操作设备。`decoder-findings.md` 是后续要求的交付物，尚未生成。也没有声称问题已解决、证据已审核或任务已可调度。

## 实际检查的材料

仅检查了以下两份被允许的 Skill 材料：

- `/workspace/scratch/fe8de3b42084/packet-source-2/claude-code/skills/adk-task-breakdown/SKILL.md`
- `/workspace/scratch/fe8de3b42084/packet-source-2/claude-code/skills/adk-task-breakdown/references/task-packaging.md`

没有读取 `telemetry/decoder.c`、`tests/test_decoder.c`、其他仓库源码或测试，也没有查找未分发的源仓 schema。当前任务只需要 research 交接，不涉及公共契约迁移，因此未读取 Skill 提及的另一份纵向拆分 reference。

交付文件已通过有限的本地结构检查：JSON 语法、19 个允许字段、字段类型、非空要求、research/forbidden/evidence-reviewed 组合、枚举值、只读模式、接收目标、报告名称及备注中的 worker 身份/父级记录。该检查只复核随包 reference，不是接收方真实 validator；接收方合同校验仍标为未验证。不得据此声称 `ready_to_handoff`。该调度属性本身也不属于 v2 顶层字段。

## Worker 身份、归属和外层信封

下表记录本次实际可知的身份信息；它不构成新的派工合同或授权。

| 项目 | 已知信息或限制 |
| --- | --- |
| 本次交接准备 worker | `/root/task_packet_consumer_b` |
| 父级派工代理 | `/root` |
| 本次 worker 职责 | 准备交接 JSON 与限制说明；未执行研究 |
| 接收目标 | `firmware-maintainer`，来自任务指令 |
| 研究执行 worker | 未提供，不得把本次准备 worker 自动视为执行 worker |
| 任务 owner | 未明确提供独立 owner 字段；接收目标不自动等于 owner。应保留上游已有 owner，不能由 worker attempt 改写 |
| 外层 worker/report 信封合同 | 未提供，因此未构造或声称验证过一个机器可用的信封 |

按 reference，owner、DAG、调度状态、worker/report 设置归外层信封，不能作为 v2 的额外顶层字段。上述信息独立保存在本说明中，避免丢失实际 worker 身份及父级归属。接收方须通过自己的既有信封合同绑定这些信息；在合同缺失时，包内 blocker 应保留。本说明不能替代信封校验，信封也不能成为权限来源。

## 原始边界与接口约束

后续研究仅允许读取 `telemetry/decoder.c` 和 `tests/test_decoder.c`。写入范围为 `[]`；禁止删除、联网和设备操作。包中未新增任何读取路径、产品修改、测试修改、运行测试、构建、执行固件或操作设备的授权。

碎片输入及返回值接口约束保存在 v2 的 `constraints` 字符串条目中。由于没有读取研究文件，不能确定函数名、签名、数据格式、缓存所有权、状态布局或返回值含义。后续须从允许读取的文件中建立这些事实，并保持原有接口；若结论依赖范围外的调用者，应记录为未解决问题，不能继续读调用者代码。

`decoder-findings.md` 应包含代码位置、边界用例证据、未解决问题，并区别现有测试断言、静态推导及未执行的新用例设想。不能把“读到测试”写成“测试通过”，也不能在没有源码时猜测具体丢尾机制。

## 接收方需处理的限制或无法判定项

1. **真实校验器缺失。** 指定材料没有提供接收方实际 validator；不能搜索其他工作目录或源仓补齐。接收方须执行自己的严格 v2 校验。拒绝时应 blocked 或 replan，不增加字段、不弱化约束、不强制转换类型。
2. **独立信封合同缺失。** 研究 worker、明确 owner、报告 transport 和信封 schema 均未提供，不能伪造。接收方应使用上游已有归属信息；本次 worker 身份及父级记录如上。
3. **报告文件与空写入范围的关系未明确。** 指令要求后续产出 `decoder-findings.md`，同时给出 `scope_write: []`。因此包保留交付物名称，但不把它解释为文件系统写入许可。若接收方已有无需研究 worker 落盘的报告通道，可按既有权限提交内容；否则文件持久化仍受阻，须由有权方处理，不能由本包补造授权。
4. **源码根目录与版本未知。** 研究路径是相对路径；准备阶段未验证存在性或绑定版本。接收方只能通过已有上下文绑定这两条允许路径，不能扩大读取范围进行探查。无法绑定时应保留阻塞。
5. **不存在执行证据。** 本次没有研究结果、运行结果、设备证据或最终审核。任何静态边界追踪均是未来研究的计划内容。是否存在尾部数据丢失尚无法判定。
6. **本次写入授权不传递给研究 worker。** 创建这两个交接文件是本次任务明确要求的准备工作；这不改变后续研究的空写入范围，也不允许清理或删除任何文件。

无需为准备工作向用户追问；上述未知项已保留为 blocker 或限制。后续只有权限、证据或合同发生实际变化时，才重新评估可调度性。
