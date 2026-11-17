# 变更提案：20261118-owned-snapshot-priority

## 背景
- main021d81aa/run44128721869 attempt1的真实Ninja回归出现bounded/[]与存活leaf；原日志SHA256 67a7e53456a9efdbe275254aa005da3bc5ce7d3eb1ca0a1cecab41edbfa79a95。helper未误报complete，但未达到后代发现/清理验收。

## 问题陈述（单问题）
- 本变更只解决全局有界扫描可能在自有进程前耗尽预算的确定性缺口。
- 宿主bounded原因未细分，不能反推具体现场原因；实际固定前缀反例将先RED后GREEN。

## 目标
- 修复有界进程快照的自有后代饥饿

## 非目标
- 不改变ADC/CMake、CI、任何预算/门禁；不生成runtime/设备/M5资格；旧ADC超时仍UNKNOWN。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约：SID与既有截止输入，限定状态快照输出。
- [x] 已识别关键风险：目录顺序、进程退出、线程、重挂父进程、PID复用与有界性。
- [x] 已明确验证命令与标准：requirements/design/tasks。
- [x] 已列补充收集：实际RED/GREEN与独立反例。

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：现有通用验证基础设施，不新增core/optional资产或框架。

## 变更重复性检查
- 已检索helper调用点及前次owned-build-session；仅当前模块和历史原patch。knowledge/L2-domain/lessons.md实际不存在，rg exit2，不伪造经验命中。
- 本次差异：前次同SID修复未覆盖无关目录前缀，新增固定顺序验收与自有优先发现。

## Breaking Change 检查
- [x] 否：不涉及兼容性破坏
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements基线：requirements.md。
- design决策：design.md，自有树优先/剩余全局查漏。
- tasks追溯：tasks.md及下表。

## Canonical Change Contract

ADK change workspace 是唯一权威变更契约。每一行必须把需求、变更语义、验收、任务、验证与证据目标连成闭环；Operation 仅允许 `ADDED` / `MODIFIED` / `REMOVED`。

| Requirement ID | Requirement | Operation | Target | Affected Surface | Acceptance ID | Acceptance Criterion | Task ID | Verification ID | Evidence Target |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | 优先发现自有后代 | MODIFIED | tests/test_skill_command_examples.py | owned snapshot | ACC-001 | 固定无关前缀后仍发现同SID各线程后代 | TASK-001 | VERIFY-001 | evidence/implementation/index.json |
| REQ-002 | 保持有界和身份安全 | MODIFIED | tests/test_skill_command_examples.py | timeout cleanup | ACC-002 | 原上限不增加且缺测不报complete | TASK-001 | VERIFY-002 | evidence/implementation/index.json |
| REQ-003 | 保持真实进程验收 | MODIFIED | tests/test_skill_command_examples.py | existing Ninja test | ACC-003 | 原测试文本不弱化且无关会话存活 | TASK-001 | VERIFY-003 | evidence/implementation/index.json |
| REQ-004 | 独立验证新来源 | MODIFIED | manifest.json | release metadata | ACC-004 | 精确full与独立审查后正常发行 | TASK-002 | VERIFY-004 | verification.md |

## 安装范围与依赖边界
- 安装范围：project-bound，仅现有测试helper；无安装动作。
- 依赖边界：已有Linux procfs/Python/Ninja，不新增依赖。

## Prompt 回归证据计划
- before/after输入：同一固定无关前缀及原真实Ninja验收；不是prompt变更。
- 失败保留：原日志/ZIP与新RED，摘要及可逆包装。

## 收敛模式与退出条件
- 当前模式：planning→execution；需求设计完成后独立实现。
- 退出条件：定向、full、独立审查；发行另需实际门禁，不提前声明。

## 备选方案与取舍
- 方案A：自有树优先，再剩余全局查漏；采用。
- 方案B：增大扫描上限/全机排序；不采用，会增加预算或依赖PID/目录顺序。
- 选型理由：保持既有有限性并优先处理本次有归属的工作。

## 风险与回退
- 不完整树不能认证整个SID清理；身份信号链不变；回退受保护后继变更，不改写历史。已有授权包括正常提交/PR/合并，发行仍经原门禁。
