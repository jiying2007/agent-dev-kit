# 重复试验效果比较

目标：落实已归档优化方案 A1 的 source/test 部分，复用现有单次 comparator 和 Run Evidence authority。

验收：显式 task/trial 集合；每条件每试验任务完整；全局 run_id 唯一；固定模型/运行时/prompt/编排模式、bundle 和上下文引用；缺失指标不当作零；基础设施失败不择优排除；统计以 task 聚类并固定重采样种子；样本不足或模型别名未验证为 inconclusive。success 与 wrong-skill 必须作为护栏；候选安全检查失败否决收益。

范围外：调用模型、执行真实运行时、独立证明调用方填写的环境/模型身份/计划登记时间、晋级产品资格。离线合成 fixtures 只验证比较器行为，不证明 ADK 提高了真实任务成功率。

保留单次 EffectCampaignInput/compare_effects 作为仍有独立用途的原子比较接口；新增重复组合接口不是兼容 shim，也不引入第二个 Run Evidence validator。SemVer 7.1.0 表示新增能力。