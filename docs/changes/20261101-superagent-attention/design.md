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

现有工作项明确绑定的 follow-up 交给原 Worker；没有明确指针时不凭主题相似合并。超 scope 必须交由可信入口重新决策。Policy revision 和人工 stop 不得被上下文覆写。

## Attention

可交付结果、不可自动恢复故障、需要明确的人类决策是通知三类。正常轮询、等待 CI、相同 blocker 的重报进入队列，不刷屏。风险升级/恢复/新 revision 必须再次可见。此行为当前由 Skill 指导，实际发送由宿主控制，不能仅因为文字规则存在就声明可用。

## Consequences

- 不迁移 DSH Runtime 和其 danger-full-access 模式。
- 不扩增 Agent/Skill/Workflow inventory 或签名/发布边界。
- 保留已有工作包 v2 校验作为权限回归，并加静态方法合同测试防止重要语义丢失。
- 后续若对 engineering-platform 实施运营投影或事件源补强，必须独立设计/测试、保护权限与副作用。

## Rollback

恢复上述 3 个已有资产的先前内容并删除新的测试即可，不存在数据迁移、运行时写入或新 provider 配置。
