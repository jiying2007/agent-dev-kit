# Negative results

- 上游 dsh-superagent 自身声明为 research prototype；本次没有执行其 pnpm/DSH/runtime 测试，也没有官方保障的生产实测。
- 上游 worktree 和 GH account wrapper 不是强沙箱，danger-full-access 同用户可读取主机其它路径：**拒绝复制执行模式**。
- 订阅 Thread 的 context-only、source dedup、策略撤销和低打扰通知，目前仅被 ADK 文本描述，不能作为真实应用/平台运行行为的 PASS。
- 现有 ADK typed task package 阻止 research/prototype 直接获得 implementation 权限，但不构成完整的 GitHub Source actor authentication、Mandate/Session lifecycle 或可靠 Outbox 证明。
- 缺少真实 UI/事件基线和固定样本 A/B；不能声称节省了多少人工注意力、Token 或事件漏读率。
- 工程平台 #228 / #229 仍是独立阻塞项；本次不改已有 Action Recovery/no-replay 权限状态。
