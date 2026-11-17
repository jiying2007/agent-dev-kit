# 随包任务消费观察

这里保留两名新上下文消费者依据实际导出的 task-breakdown Skill 准备研究交接的原始产物。共同任务是为 firmware-maintainer 准备 decoder 碎片输入研究；仅允许读取两个指定文件，禁止产品修改、删除、联网及设备操作，产物应保留接口约束与 worker 归属。本次只生成交接，不执行研究。

消费者只可读取各自指定的 Skill 和同包 reference，没有得到产品 validator、仓库测试、缺陷诊断或预期答案。协调者事后使用当前生产 `validate_task_package` 检查原始 JSON，不先修改消费者产物：

- 旧导出消费者生成了候选，但明确标为未验证、不可派发。生产 validator 返回缺少 15 个字段、增加 11 个字段。
- 新导出消费者生成完整 19 字段的 research 包；生产 validator 返回空 errors tuple。scope、接口约束、空写范围均保留；外层信封和 worker 归属另存 notes，没有凭空增加顶层字段或实施权限。

产物通过 v2 结构校验不表示下游任务已经运行，也不表示外层信封、worker 绑定或报告保存通道已经验证。新消费者如实保留这些 blocker；本观察不强行清除它们。

这是**开发阶段的一次消费观察**，用于确认随包说明能否支持有效 JSON。它不是预注册配对 A/B：两次任务表述并非逐字锁定，owner/接收目标表述有差别，没有随机化、重复样本或效果归因。不得据此宣布整体模型能力、Native discovery/load/trigger、Token、费用、延迟或真实固件效果提升。正式 `skill_method_ab_prereg.json` 活动继续保留未执行状态和零模型试验计数；本观察是独立的内置协作消费任务，不能计入该活动。

`observation.json` 绑定原始消费者文件、所读导出文件和实际 validator 的摘要及返回值。原始 JSON 和 notes 不进行格式修正或结果美化。
