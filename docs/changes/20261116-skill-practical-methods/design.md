# 设计

需求：@docs/changes/20261116-skill-practical-methods/requirements.md。

- Review 在既有 reference 选择单一 diff 端点和对应 check，明确 whole-branch baseline 与 dirty overlay；真实导出模板在受控 Git 仓验证目标内容，不仅检查 exit 0。
- Context 保留既有最小交接字段和证据/权限边界，将 ADK 源仓辅助文件改成可核条件；默认正文自足，避免重复 schema 或增加强制依赖。
- ADC 在乘法前拓宽，并通过编译期约束声明可安全支持的 int 宽度；测试预期来自零点、满量程、钳位及无效输入，不复制实现公式。接入现有 command-example 测试，不新增顶层测试编排。
- 实现集成补充（独立 reviewer 核可）：`_Static_assert` 位于 ADC 实现，既有 CMake 目标用 PRIVATE `c_std_11`，cross smoke 明确 `-std=c11`。公共头与测试不需传播额外标准要求；真实 ADC CMake 构建进入同一 fixture 类，本地缺工具仍不算执行。
- 堆工具仅修正当前映射；不把 Valgrind 插桩时间当原生性能。flaky 细节放现有 optional reference；协议在既有 Retry boundary 中替换重复说明。三者是方法改进，受控逻辑反例只说明诊断维度，不冒充 agent A/B。
- CMake 用互斥的 preset / manual 路径，传递实际构建目录与 configuration，分析实际 ELF；测试使用真实 CMake/CTest，单独记录宿主工具不足。保持 host-unit / compile-only / emulator / board-runner 的区别。
- 逐 Skill 等量压缩重复说明；large-refactor 总源码目前仅余 6 B，所有原 ratchet 必须保持。研究、历史反例和审查说明放本 change，不进入运行时 Skill。

职责：root 当前负责设计/集成与 protocol/flaky 方法；general 实现者负责 Review/context；practical 实现者负责 ADC、性能与 CMake；external 研究者保持独立只读审查。源码实现前先完成本设计预审。所有实现者只写分配路径，用 apply_patch；root 独占版本/fixture/catalog/最终提交。

回滚：按本轮原子提交独立 revert，恢复上一不可变组件发布；不改历史测量或产品资格。发布仍走普通 PR、最终 HEAD 检查、main CI、tag/Release 核验。
