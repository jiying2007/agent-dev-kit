# 独立终审后的 OTA / VxWorks 回归修复

状态：完成并释放源码，供 coordinator 执行最终完整回归和独立复审。原 T3b 的审查、RED/GREEN 和首次实现记录没有覆盖。本目录专门记录此次终审反馈后的修正。

## 确认的问题

独立终审的 `skill-usability-review/review-probes.json` 证明以下三个请求在基线 `78c3be7f6f9b5ee2e557de54156532fb3169198d` 选择 production-field-readiness，首轮实现却返回 needs-triage：

1. 评估嵌入式设备 OTA 的断电恢复、回滚和上线 readiness。
2. 请只读检查 OTA 签名和回滚验证证据。
3. Review OTA firmware rollback readiness。

首轮实现将领域条件收窄为连续的 `OTA升级/OTA回滚/OTA验收`，误拒绝肯定 OTA 领域中插入其他词的实际请求。单纯恢复 OTA 又会暴露原局部否定只识别紧邻 marker 的限制：`不涉及量产或OTA` 中第二项仍被当作肯定领域。本轮 RED 进一步复现了 `不涉及量产、OTA和RMA` 的同类问题。

此前 102-suite 完整运行被 coordinator 停止，退出 130，停止时 42 项通过；本组没有把该中断运行算作整套通过。

## 最小修正与边界

Coordinator 更新 design 后授权只修改 `implicit_context` eligibility：

- production-field 元数据恢复肯定 `OTA` 领域条件，不添加完整任务句名单。
- `_has_affirmative_context` 只在已经声明的领域词之间，沿紧邻的 `或/和/与/及/、/and/or/nor` 继承首项的否定。句号、逗号、分号、其他词或新的动作打断这个紧凑名单。
- 连接判断固定检查 8 个连接词，并在 `negated_ends` 集合反查位置；不逐次扫描所有先前否定项。没有增加性能门禁，也不声称实测效率提升。
- 原 `_is_locally_negated`、`_active_phrase_matches`、action/mode 分类和 permission 合并逻辑保持不变。`snapshot.json` 对 9 个原 helper 做源码文本一致性检查，均为 true。
- 引述/fenced code 的既有剔除保留；单纯 inline formatting 仍可表达肯定领域。显式只读、肯定 OTA 后附“禁止刷写”以及数据库回滚控制均保留。

VxWorks 源修改由 embedded 作者完成，只向 RTOS 的已有领域条件追加 `/VxWorks`。本组仅整合共享矩阵正例及明确否定 VxWorks 的对照，没有修改 RTOS 文件。

## RED → GREEN

| 验证 | 结果 | 原始文件 |
| --- | --- | --- |
| 新正反验收的 RED | 3 methods，14 failing subtests，exit 1 | `red-tests.{json,txt}` |
| 原始路由及单独恢复 OTA 的 eligibility 对照 | 3 条真实 OTA 被拒绝；仅恢复词条会错收并列否定 | `red-probes.json` |
| 修正后的共享完整触发矩阵 | 25 methods PASS，exit 0 | `trigger-matrix.{json,txt}` |
| 路由 IR 合同 | 4 methods PASS | `routing-ir.{json,txt}` |
| 现有 CLI 边界回归 | 39/39 PASS | `match-boundary.{json,txt}` |
| 现有 CLI 匹配及附带 IR 回归 | 41/41 + 4 methods PASS | `match-effectiveness.{json,txt}` |
| Ruff / strict mypy | PASS | `ruff.{json,txt}`、`mypy.{json,txt}` |
| 模块预算与架构规则 | PASS | `module-budget.{json,txt}` |
| 8 个原 profile ratchet | 全部 PASS，ratchet 文件未变 | `snapshot.json` |

矩阵覆盖原三个 OTA 回归、多项中英文并列否定、句/逗号/分号和新动作打断、否定列表后重新提出肯定 OTA、肯定 OTA 后禁止刷写、inline formatting、引述/fence 以及原域外控制。原三条请求恢复对应 routing/skill_trigger 来源，mutation permission 仍为 deny；显式只读请求仍为 readonly/E0。

`probe.py` 保存真实 matcher 和 eligibility 输出；`verify.py` 重放相关既有入口；`snapshot.py` 固定源码哈希、原全局 helper 一致性及原预算。所有记录都是源码工具行为，不是 live runtime、模型或设备验收。

## 最终快照与交接

- Manifest 保持 **11.3.14**，此次修正没有写 Manifest。
- Production-field Skill 较首次 T3b 交付 **−26 B**。
- `_matcher_kernel.py` 为 **29,269 / 30,000 B**。
- Large-refactor full 为 **323,280 / 323,328 B**，余 **48 B**。
- Embedded-fullstack full 为 **316,398 / 316,854 B**；incident-response 为 **46,515 / 46,612 B**。
- 逐文件 SHA-256 和差额见 `snapshot.json`；`cumulative-owned.diff` 是相关三个文件相对冻结基线的累计差异。

本组不再写源码。最终完整 102-suite、精确最终源码的独立复审及后续发布/Root 消费仍由 coordinator 负责；本记录不冒充这些后续步骤的完成证据。
