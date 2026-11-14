# 65 Skills 全量优化要求（source-only）

- 全部 56 core + 9 optional 必须在冻结 Manifest 身份台账中一一列出，逐项说明保留或改造。未修改 ≠ 认证无问题。
- 按前述官方/社区优质 Skills 方法做职责、触发、信任、工具适用性、输出证据、成本/上下文冗余比对。只修改证据明确的薄弱点，不给所有 Skill 加重型模板/平行路由权威。
- 本轮优先完成 11 项：URL/IMAP/data-fetch、供应链、flaky、Skill 组合、协议、MCU 单测、寄存器、性能、CMake；完整/安全模型授权和设备写路径保持原 fail-closed。
- 所有新负例使用既有 tests/test_skill_content.sh 注册，Runner/Manifest/permission contract 不扩容，系统 Python 不新增依赖。
- Release/Root 需 exact main CI 与不可变发布证据；E2–E4 native host、Token、任务质量和设备运行不得由源码或 fixture 冒充。
