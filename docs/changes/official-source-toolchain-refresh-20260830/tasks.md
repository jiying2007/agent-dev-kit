# 任务：official-source-toolchain-refresh-20260830

| 阶段 | 状态 | 完成标准 | 验证 |
|---|---|---|---|
| S1 盘点与来源核验 | complete | 28 条逐条打开，Codex manual 已刷新 | source-review |
| S2 freshness 落地 | complete | manifest/reference 日期与决策一致 | official docs + timezone tests |
| S3 Python launcher | complete | 选择顺序和降级语义有回归 | test_python_launcher |
| S4 收口 | complete | strict 与适用门禁有新鲜证据 | verification-evidence |

## 执行控制

- owner：T3 source/toolchain subagent
- verifier：父 Agent 交叉验证 + deterministic gates
- retry budget：同一根因最多 2 次，第三次前 replan
- staleness threshold：45 分钟或任一阶段完成时更新
- heartbeat：每完成一个阶段更新本表和验证证据
- stop condition：`pass | replan | split | blocked | abort`
