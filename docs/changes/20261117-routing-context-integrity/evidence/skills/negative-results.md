# 本轮负结果与修正记录

1. 基线的 19 个定向 source matcher 探针只有 7 项满足目标；原始输入/完整返回见
   `routing-before.json`。最初新增的 3 个测试方法共发现 15 个失败子例；没有修改原固定评测。
2. requested_action 最初被关闭附加属性的 manifest schema 拒绝，三方法无法加载 manifest。
   在原 schema 增加可选 stringArray 字段后恢复；新测试验证删除该可选类的旧 manifest 仍有效，
   非字符串数组项被拒绝。未新增 schema 文件、强制字段或 IR 版本。
3. 新测试初稿把 driver 的 `live_device_authorization=not-required` 误解为设备授权，预期
   `explicit-required`。实际该选中能力范围仅 workspace，escalation_effects 为空；测试改为
   验证 workspace scope 与无设备 effect，不修改产品权限。另一个 `审查代码…` 负例原本不在
   review 触发词表，改为只验证 ADR 不得误选；该 prompt 保留，没有扩围增加 review alias。
4. 合并跨触发组的否定跨度时，曾消费 `_phrases` generator 后再遍历它，导致 lexical fallback
   丢失，56 测试组在中间版本出现 51 个失败子例。将 trigger_sets 固定为 tuple 后，原所有
   governance、fallback、域条件与新增路由测试通过。没有改失败场景的原期望来变绿。
5. 中间 `_matcher_kernel.py` 实测 31,502 bytes，超过原 30,000 bytes 模块上限；没有放宽预算。
   全仓调用点检索确认纯格式化函数仅由 canonical matcher 使用，将其原样迁入已有
   matcher.py 格式化入口，删除内核不再需要的 json import。最终内核 29,107 bytes、
   canonical matcher 20,779 bytes；原 module 检查通过，未增加支持模块或遗留例外。

最终定向结果在 `routing-verification.json`；完整集成/独立审查不在此记录冒充已完成。
