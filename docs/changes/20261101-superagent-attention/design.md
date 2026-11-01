# Design — 在现有 ADK 入口增量吸收

## Single authority

ADK 仍为平台中立资产和执行策略约束。Source/Trigger/cursor、Worker Slot、Action Gateway、Outbox 和实际恢复由外部宿主/engineering-platform 管辖。新约束是对现有 Skill 的方法行为要求，不新增并行状态机或 host authority。

## Decision flow

```text
untrusted Source/Thread/CI body  ->  evidence/context only
                           |
trusted source policy + owner/authority -> intake decision
                           |
               existing Task/WorkItem (stable ID)
                           |
          Worker attempt + checkpoint + evidence
                           |
     current verification/result or human action
```

现有工作项明确绑定的 follow-up 交回原 WorkItem/owner，由可信 Router 在当前授权/策略版本下重新确认 Assignment 与可用的 Worker attempt；不得假设原 Worker 实例仍存活。没有明确指针时不凭主题相似合并。超 scope 必须交由可信入口重新决策。Policy revision 和人工 stop 不得被上下文覆写。

## Attention

可交付结果、不可自动恢复故障、需要明确的人类决策是通知三类。正常轮询、等待 CI、相同 blocker 的重报进入队列，不刷屏。风险升级/恢复/新 revision 必须再次可见。此行为当前由 Skill 指导，实际发送由宿主控制，不能仅因为文字规则存在就声明可用。

## Consequences

- 不迁移 DSH Runtime 和其 danger-full-access 模式。
- 不扩增 Agent/Skill/Workflow inventory 或签名/发布边界。
- 保留已有工作包 v2 校验作为权限回归，并加静态方法合同测试防止重要语义丢失。
- 后续若对 engineering-platform 实施运营投影或事件源补强，必须独立设计/测试、保护权限与副作用。

## Rollback

区分方法撤销和完整源码回退：

- **仅撤销方法规则**：恢复原有两个 Skill 及 `docs/agent-operating-rules.md`，撤销新增 Python 单元测试与它在现有 `tests/test_intent_boundary_governance.sh` 的调用。
- **完整 PR 回滚**：必须在受保护分支通过正式 revert/new-change 流程处理本 PR 全部改动，包括 `manifest.json`、`pyproject.toml`、`.version-lock`、`README.md`、`CONTEXT.md`、`CHANGELOG.md`、`src/agent_dev_kit/__init__.py`、`manifests/software_m5_eval_contract.json`、测试/方法与 `docs/changes/20261101-superagent-attention`，重新核版本 SSOT、原生 CI、独立审查与 Root Gitlink/lock 关联。**已发布的 immutable tag/Release 不可篡改或删除**；发布后回退需新的版本、来源绑定证据和正常提升流程。不存在本次变更新增的数据库迁移或 provider 配置。
