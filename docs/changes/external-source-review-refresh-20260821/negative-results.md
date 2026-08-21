# Negative Results

| Attempt | Result | Decision |
| --- | --- | --- |
| `validate --strict` 与完整回归 | 三项来源在 `2026-08-13` 到期，完整回归 51/59 | 不放宽 checker；重新读取官方来源后刷新 30 天窗口 |
| 仅把 registry namespace ownership 当作信任结论 | 官方机制只证明发布 namespace 控制 | 保持 listing 仅用于 discovery/provenance，安装仍需独立审查 |
| 把 GenAI conventions 当稳定 schema | 官方仓 Schema URL 仍为 TODO，模型持续演进 | 保持 optional、version-pinned、敏感内容默认关闭 |
