# 历史发行补发保留 latest：真实失败

## N01：成功补发旧版本使 latest 回退

- 原始工作流：[44211407809](https://github.com/jiying2007/agent-dev-kit/actions/runs/44211407809)，整体 conclusion 为 success。
- 当前发行：[v11.4.3](https://github.com/jiying2007/agent-dev-kit/releases/tag/v11.4.3)，source `bf292c412ae12168dd09a76b6edcb945f3dbdcd1`，published_at `2026-11-18T00:58:32Z`，immutable 为 true；package job `134490516961` 通过 61/61 smoke。
- 历史补发：[v11.4.2](https://github.com/jiying2007/agent-dev-kit/releases/tag/v11.4.2)，source `0a6bf985de5e2d3523cd4e82cb19d3b8575a4fdb`，published_at `2026-11-18T01:07:40Z`，immutable 为 true；repair job `134493685944` 对自身 source 完成 102/102 回归，未借用新版本 CI。
- 观察：`2026-11-18T01:09:31Z` GET `/repos/jiying2007/agent-dev-kit/releases/latest` 返回 release ID `449392361`、tag `v11.4.2`。这是实际顺序下的 latest 回退；精确版本的标签和资产没有改变。
- 原因：创建 release 的命令未显式传入 latest 策略，历史补发沿用同一默认创建行为。
- 修复与验证：以新候选明确 current/backfill 身份和创建参数，保留原发行证据；回归、独立审查、新版发行和 Root 消费以各自实际回执判定。新版本发布前不将此问题标为已修复。

同一工作流的两个同名 artifact 均已成功上传，本次没有观察到命名冲突，因此不以推测的冲突扩大修改范围。本记录不代表已验证跨工作流并发顺序、模型效果或现场资格。
