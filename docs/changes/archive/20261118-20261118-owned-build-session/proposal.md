# 变更提案：20261118-owned-build-session

## 背景
- ADK main 15fa31d1 的两次 hosted ADC/CMake 15秒超时仍为原因未知，run 44116100760 的唯一复验已耗尽，不再触发 attempt 3。
- 2026-11-17T16:07:48Z 一次独立真实 Ninja 合成实验确认：helper 返回 cleanup=complete 时，同 SID、新 PGID 的规则 shell 和 Python leaf 仍存活。此为独立可复现缺陷，不是原15秒超时的原因证明。

## 问题陈述（单问题）
- 本变更只解决一个明确问题：既有 timeout helper 漏掉自有会话的新进程组并误报清理完成。
- 触发证据：post-attempt2/ninja-cleanup-probe-result.json；本地 Ninja 1.11.1.git.kitware.jobserver-1，原helper SHA256 301fb52ff31802f2601b6a8baf3416380735c420371a5d0fa22bc4913c461461。记录随后按原字节纳入 evidence。

## 目标
- 修复构建示例超时遗漏子进程组

## 非目标
- 不修改 ADC/CMake 示例、生成器、编译优化、测试顺序、原默认15秒work、1秒cleanup、CI必需项或资格标准；不新增Skill、runtime、依赖或权限。不宣称修复历史 hosted 超时。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约
- [x] 已识别关键风险（并发/边界/性能/兼容）
- [x] 已明确验证命令与通过标准
- [x] 若信息不足，已列出补充收集计划

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- [ ] 属于场景化能力（optional）
- 归属结论与理由：既有仓库测试基础设施，不形成新的安装能力或生产公共接口。

## 变更重复性检查
- 已检索既有 helper 全库调用点与测试替身；knowledge/L2-domain/lessons.md 不存在（rg exit2）。
- 既有快照只按PGID筛选，本次差异是已经有真实同SID/异PGID存活反例；不重复未知超时的盲重试。

## Breaking Change 检查
- [x] 否：不涉及兼容性破坏
- [ ] 是：涉及兼容性破坏（必须补充迁移与回退计划）

## Spec 链路检查
- requirements 基线：@requirements.md。
- design 决策：@design.md。
- tasks 追溯关系：@tasks.md。

## Canonical Change Contract

ADK change workspace 是唯一权威变更契约。每一行必须把需求、变更语义、验收、任务、验证与证据目标连成闭环；Operation 仅允许 `ADDED` / `MODIFIED` / `REMOVED`。

| Requirement ID | Requirement | Operation | Target | Affected Surface | Acceptance ID | Acceptance Criterion | Task ID | Verification ID | Evidence Target |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | 观测自有会话内不同进程组 | MODIFIED | tests/test_skill_command_examples.py | timeout snapshot | ACC-001 | 真实Ninja leaf入快照且无关session不入快照 | TASK-001 | VERIFY-001 | evidence/implementation |
| REQ-002 | 安全清理并诚实报告 | MODIFIED | tests/test_skill_command_examples.py | timeout cleanup | ACC-002 | 自有leaf退出、无关session存活、身份漂移和缺测不得误杀或报complete | TASK-001 | VERIFY-002 | evidence/implementation |
| REQ-003 | 保留预算、双流及失败历史 | MODIFIED | tests/test_skill_command_examples.py | timeout contract | ACC-003 | 原15秒和1秒上限、正常退出、双流、旧失败原件保留 | TASK-002 | VERIFY-003 | verify-report.md |
| REQ-004 | 回归和独立证据可追溯 | ADDED | docs/changes/20261118-owned-build-session/evidence | source verification | ACC-004 | 真实RED/GREEN、full及独立Spec/Quality绑定准确源码，未完成发行不预认证 | TASK-002 | VERIFY-004 | evidence/implementation/index.json |

## 安装范围与依赖边界
- 安装范围（global-ready/project-bound）：project-bound测试基础设施。
- 依赖边界（脚本/数据/上下文）：现有Python标准库、Linux procfs和已有Ninja，不新增依赖。

## Prompt 回归证据计划
- before/after 对比输入：固定真实Ninja反例；此项为执行代码回归，不是Prompt效率宣称。
- 失败样例保留方式：原两次main日志/ZIP摘要、独立RED与修复GREEN分开保存，不覆盖。

## 收敛模式与退出条件
- 当前模式（diagnosis/repro/planning/execution）：execution，仅修复已证实helper缺陷。
- 退出条件：真实RED→GREEN、共享helper full、独立Spec/Quality及新候选原门禁通过；未知超时仍独立保留。

## 备选方案与取舍
- 方案 A：自有SID身份核对、标准库pidfd、有界清理和保守状态。
- 方案 B：只新增更多日志或重跑旧CI。
- 选型理由：A修复独立已证实的真实缺陷；B不能修复遗留子进程，故不采用。

## 风险与回退
- 误杀、漏杀、误报complete是主要风险；以归属/身份/负控制和缺测fail-closed约束。回退锚15fa31d1，通过受保护后继变更恢复文件；失败、标签及不可变发行资产不重写。
