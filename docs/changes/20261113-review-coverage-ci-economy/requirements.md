# Skills 质量/验证开销优化要求（11.2.14）

- 对完整且高风险 Review 建立按范围/快照的已检查、未检查和无法读取证据；仅核单条反馈不加完整账本。缺关键验证与独立风险决定不得通过。
- 安全/兼容补丁在已授权隔离环境内按需验证原缺陷、同根因变体、合法行为与新引入风险；缺运行条件标 not-tested。
- C/C++、BSP 方法先根据 linux-embedded / mcu-rtos / mcu-baremetal 与编译器、sysroot、Zephyr/Kconfig 等真实目标选择，不隐式运行/安装工具、刷机或声明零风险。
- 将廉价的 catalog、content、trigger 与 full-only SOP 测试排到完整大回归之前；不得删除 102 套和高风险门禁，quick 仅新增 catalog 一项（61 套）。
- 复用既有 effect_trials 和真实 trace/eval 规范；不新建 runner、模型调用链、定时任务或经济硬上限；真实 E2–E4 效果为 not-measured，直到可核原始 trace。
