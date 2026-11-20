# 交付切片

- TASK-001 (REQ-001/ACC-001)：丰富 Explore/Challenge 反证和快速退出；验证内容/触发边界。
- TASK-002 (REQ-002/ACC-001)：使现有需求、接口、任务及 feature-delivery 使用同一 Delta 合同；验证正负场景与轻量逃逸路径。
- TASK-003 (REQ-003/ACC-001)：双仓协议契约验证路径；无真实设备时仅为方法设计，不声称联调完成。
- TASK-004 (REQ-004/ACC-001)：清除错误的 legacy script 可运行引用；运行回归。
- VERIFY-001：`python3 -m unittest tests.test_spec_driven_delivery -v`（确定性源码合同），随后 CI 全量回归。
- VERIFY-002：真实行为 A/B 与当前 native Host 未运行前标 `not-measured`。
