# Task Cost Profile

```yaml
task_cost: micro | standard | complex | high-risk
primary_skill_budget: 0 | 1
planning: none | inline | change-artifacts
hub_preflight: skip | conditional | required
context_budget: small | medium | large
read_tier: L0 | L1 | L2 | L3
verification_tier: targeted | regression | full-gate | audit
archive_candidate: no | conditional | required
escalation_condition: ""
```

| task_cost | 默认执行成本 |
|---|---|
| micro | 不加载 skill、不查 Hub；直接修改并定向验证 |
| standard | 最多一个 primary skill；项目事实相关时才查 Hub；定向测试 |
| complex | 一个 primary skill，可有 supporting；先计划，small Hub 预检，按风险回读原文 |
| high-risk | 一个 primary skill；L2/L3 原文、完整 gate、审批与回滚，不以省 Token 降级证据 |

判级先于词法 skill 匹配。相邻 skill 不叠加为多个 primary；路由零命中且任务为 micro/standard 时允许直接执行。
