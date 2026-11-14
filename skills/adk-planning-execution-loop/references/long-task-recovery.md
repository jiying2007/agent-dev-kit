# Long Task Recovery Template

## Task State

- Task:
- Current stage:
- Last completed checkpoint:
- Current blocker:
- Changed scope:
- logical_task_open: true | false
- milestone_close: true | false
- session_handoff_required: true | false
- Retry budget:
- Staleness threshold:
- Heartbeat:

## Review Convergence

- Review round:
- Review mode:
- Finding classes:
- New finding class count:
- Consecutive clean reviews:
- Contract change decision:
- Replan reason:

## Checkpoints

| Stage | Status | Done Criteria | Verification | Evidence |
|---|---|---|---|---|
| S1 | pending |  |  |  |

## Goal Closure

- Goal statement:
- Completion claim:
- Claimant:
- Verifier:
- Required evidence:
- Open items:
- Stop condition: pass | replan | split | blocked | abort
- Decision: pass | needs-fix | blocked

## Validation Resource Matrix

| Validation | Output directory | Binary/cache/device | Parallel decision |
|---|---|---|---|
|  |  |  |  |

## Recovery Prompt

```md
Goal:
Completed:
Current state:
Do not repeat:
Next action:
Required verification:
Retry budget:
Staleness threshold:
Open items:
```

## On-demand execution branches

以下仅在对应条件触发时加载，不是每轮默认检查清单；适用原宿主/项目更严格合同仍优先。

- **受控生命周期或外部写入**：涉及 OTA、生产设备、权限、迁移或发布，冻结 owner × state × event × resource × termination × invariant；核对原审批、回滚锚点和写入结果。网络/工具回执未知时先对账，不盲目重放。
- **Task Package v2**：真正派工才写 kind/question/evidence/permission/exit/handoff/retention、scope_read/scope_write/must_not_touch。decision/research/prototype 不可获得 implementation 权限，缺依赖或原文审查时须先退回规划。
- **Evidence / attestation**：验证必须能从原验收 criterion ID 和注册 evidence digest 追溯。新增测试计数、流水号和 heartbeat 不证明目标收敛。attestation 写入后回读；未通过不能声称完成或归档。
- **风险与恢复**：发现设计/共享契约/重大 finding 变化时 replan；两次相同失败仍无根因先更新假设。计划偏差不按固定百分比机械重审：只在范围、原验收分母、权限、依赖或验证路径实质改变时启动适用审查。三次 blocker 是诊断信号，不自动升级某个组织层级。
- **最小充分验证／避免重复全量流程**：对已批准计划的低风险阶段，按 `change_snapshot / affected_interfaces / prior_verified_snapshot / evidence_freshness` 选择最小受影响检查；相同快照且结果仍有效时复用原始回执并写明 `verification_reused / reason`，不要重复调用模型或重新跑整个 Goal。若输入、依赖、设备状态、权限或发布边界变化，旧证据失效；阶段 checkpoint 不替代最终要求的完整回归、独立 Review 和真实现场门禁。未运行且不可复用则 `not-tested`，失败仍保持 needs-fix。
- **并行验证**：执行前核共享构建目录、缓存、端口、二进制或设备资源；相互冲突串行。阶段末收敛 orphan checkpoint，只保留通过/失败的可重放证据和真实恢复入口。
- **Goal Closure**：原 goal_statement、completion_claim、claimant、独立 verifier、required_evidence、open_items 与 stop_condition (pass/replan/split/blocked/abort) 均需可追溯。当前预算、历史预算合规和证据验真分别报告；阶段 milestone 不调用整体 final，也不能自动完成父 Goal。
- **Runtime 限制**：仅当宿主报告真实 stop 才停止实施并依现有权限重规划；不增加人民币日费用硬限制。纯 Skill 不能读出宿主私有 Goal、控制 scheduler 或自签审批。外部原始证据缺失时 UNKNOWN，不能因压缩摘要而放行。

## Recovery handoff discipline

新会话开始只读最近的可信 checkpoint、当前验收、开放的阻塞、已核验 source SHA 和最多三个 READY 动作。事件相同且上次动作成功时不重复调用模型；只有用户指令、HEAD、失败、新证据或审核要求变化，才更新派工。原始日志保留 raw_ref 并在高风险或语义冲突时按需回读。

## Interrupted effects and observable progress

中断点涉及发布、迁移、评论或设备写入时，用原 operation ID、目标身份和原验收对账：可信回执已证明完成则只补索引/checkpoint；已证明未开始且原授权仍有效，才可重试；结果仍未知则阻塞该依赖，继续其他已批准且无冲突的 READY 工作。进程退出、缺少本地文件或旧 checkpoint 的 `unknown` 不等于外部操作未发生，不得换一个 ID 重新发送。

每次继续执行至少指出实际变化的验收项、产物身份或新诊断证据；改写计划、更新时间和重复查询不算进展。相同输入、同一动作、同一失败连续两次且没有新信息时，停止重放该动作，修改一个可证伪假设或报告具体 blocker。已完成子项保留原产物与回执；新阶段完成只关闭自身验收，未完成的父 Goal 分母仍保留。
