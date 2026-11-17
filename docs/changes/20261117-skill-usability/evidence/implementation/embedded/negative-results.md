# T3a 负结果

1. **预期 RED：RTA 模型条件缺失。** 在原三个 Skill 正文未修改时，先加入验收派生的 `RtosResponseTimeModelTests`，执行 `python3 -B -m unittest -v tests.test_skill_rtos_methods`，exit 1；5 项中只有模型适用条件检查失败。`优先级固定且互异` 在原适用条件中不存在。原 tick 测试和独立算术对照通过。原日志：`t3a-rtos-red.log`。
2. **预期 RED：五个调用反例。** `t3a_checks.py` 原11项仅6通过；销售任务/无RTOS裸机误选、仓内BSP fixture漏选、两条DMA预算任务误排除均按审查重现。原结果：`t3a-routes-red.json`。没有把这次失败当工具故障重试或更改期望。
3. **实现期非回归失败：BSP-only 领域条件过窄。** 第一版已让原11项通过，但它会排除本 Skill 原先声明的 `SoC board 迁移分析`。新增该原触发控制后12项中11通过，唯一失败为 `bsp-existing-soc`，见 `t3a-soc-control-red.json`。本次差异是补回真实已存在的 SoC 领域，不是重跑原失败路径；将 implicit_context 改为 `BSP/SoC` 后12项全过。
4. **Build 前经验检索负结果。** `knowledge/L2-domain/lessons.md` 不存在；未宣称召回或引用不存在的历史经验。

没有真实设备或 Agent runtime 的失败/成功记录；测试与观察限制在源码、host 算术、确定性 matcher 与离线 compiler。
