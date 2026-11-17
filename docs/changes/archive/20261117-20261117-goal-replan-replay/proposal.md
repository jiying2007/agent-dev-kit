# 变更提案：20261117-goal-replan-replay

## 背景
在用户授权的全面优化中，独立 reviewer 从既有 canonical reducer 复现历史 replan 重放；原始输入及 before 结果已冻结。

## 问题陈述（单问题）
goal.updated 只比较当前 attestation，导致 A→B→A 在新 event_id 下被接纳。该问题是既有确定性历史消费检测缺口。

## 目标
拒绝已消费 intake attestation，同时保持全新有效 replan、事件幂等与保守 trust floor。

## 非目标
不添加宿主权限体系、adapter、持久总账或外部副作用执行；synthetic verifier 反例不证明真实宿主已被绕过。

## 上下文充分性检查
- [x] requirements.md 固定正负控制和证据限定。
- [x] 已识别旧日志重放、兼容 intake 和事件幂等边界。
- [x] 已冻结独立输入与生产函数复验命令。
- [x] 实际宿主恢复场景继续由宿主验证。

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- 归属结论：修复既有 execution_policy reducer，不创建新权威。

## 变更重复性检查
现有测试覆盖同 event_id、错 Goal/摘要、旧 checkpoint 和 verifier 缺失；本次新增历史 attestation 装入新 event_id 的实质不同反例。

## Breaking Change 检查
- [x] 否：拒绝错误历史重用，合法新 replan 及既有输入/输出 schema 不变。

## Spec 链路检查
requirements.md 定义验收；design.md 约束局部集合与角色分离；tasks.md 绑定测试和独立冻结探针。

## Canonical Change Contract

| Requirement ID | Requirement | Operation | Target | Affected Surface | Acceptance ID | Acceptance Criterion | Task ID | Verification ID | Evidence Target |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | 拒绝历史凭据重放 | MODIFIED | execution_policy/reducer.py | goal.updated | ACC-001 | A→B→A 新 event_id 被拒绝且不依赖 verifier | TASK-001 | VERIFY-001 | verify-report.md |
| REQ-002 | 保持合法重规划 | MODIFIED | tests/test_execution_policy.py | existing reducer contract | ACC-002 | 新 C 接纳，事件幂等和保守 floor 保持 | TASK-001 | VERIFY-002 | verify-report.md |
| REQ-003 | 保持信任拒绝 | MODIFIED | tests/test_target_contracts.sh | native trust verifier | ACC-003 | 拒绝、异常及 truthy 非 True 不取得信任 | TASK-002 | VERIFY-003 | verify-report.md |
| REQ-004 | 原始反例与安全回归 | MODIFIED | change evidence | independent review | ACC-004 | 冻结输入复验、完整回归与独立审核通过 | TASK-003 | VERIFY-004 | verify-report.md |

## 安装范围与依赖边界
现有 core global-ready 资产，无新依赖；在 reducer 完整事件归约中检查历史，不改变实际宿主准入职责。

## Prompt 回归证据计划
本变更无 Prompt 改动；N/A 由 diff 与原始程序反例证明，不执行模型测量。before 原始输入不改，after 另存。

## 收敛模式与退出条件
execution。独立旧 A 拒绝、新 C 接纳、完整安全回归和 Spec/Quality 通过后收敛；真实宿主证明保持未认证。

## 备选方案与取舍
选择现有归约局部历史集合；拒绝禁用所有 mode change、相信新 event_id 或另建持久账本，避免破坏合法流程与权威边界。

## 风险与回退
旧错误日志会明确被拒绝；不得静默吞掉已重放的变更。受保护 revert 与 Root gitlink 回退可恢复源码，原始证据永久保留。
