# 设计说明：workflow-verify-fail-closed-v1

## 架构影响
- D1：`run_verify_checks` 显式组成短路链，任何前置 gate 非零立即返回，不运行后续 gate。
- D2：外层 workflow 继续负责写 `verified | verify-failed`，状态机接口不变。

## 数据与配置影响
- D3：无 schema/config 变化；verify report 保留首个失败输出，state 固定为 `verify-failed`。

## 兼容性与迁移方案
- 成功路径命令顺序不变；只有此前错误放行的失败路径改变。

## 验证策略
- 新测试复制真实 `workflow.sh`，注入 validate exit 23 + format exit 0，断言 verify 非零、
  `stage: verify-failed`、format 未执行。
- 运行 `test_workflow.sh`、quick/full parity 与 change verify retry。
