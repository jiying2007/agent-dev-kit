# 负例记录：agent-value-lifecycle-v1

| 假设/风险 | 确定性注入 | 结果 | 决策 |
|---|---|---|---|
| 合同可提升只读 Agent 权限 | 将 requirements-analyst 改为 code-write | fail-closed | permission rank 与 effect/tool allowlist 同时受 manifest ceiling 限制 |
| 合同可增加新 handoff | 注入 unknown-agent | fail-closed | handoff 必须存在且与 manifest 关系一致 |
| 数量或 Token 可进入质量 KPI | 注入 report-count/tokens-per-task | fail-closed | 仅允许进入 diagnostic-only 集合 |
| 缺 Agent 合同仍可通过 | 删除一个 Agent contract | fail-closed | 合同 ID 与 live manifest Agent 集合必须严格相等 |
| 测试值可冒充 runtime usage | 将 emitter 改为 measured/enabled | fail-closed | 第一阶段固定 not-measured/disabled/none-claimed |
| 无 receipt 也能产生 measured/零值 | 空输入调用 measured emitter | fail-closed 为 `not-measured`，不输出 metrics/source count | unknown 不得转换为零 |
| 同一 invocation 可重复计入价值 | 重复 receipt_id 或资产+layer+invocation_ref | fail-closed | 防止 replay/double count |
| test evidence 可混入 runtime 结果 | 同资产输入 test/runtime receipt | 输出两个 evidence-layer measurement | 不跨证据层聚合 |
| 缺可选观测可按零计算 | 不提供 escaped_defect/rollback/time | 每项显式 `not-measured/field-not-observed`，无 value | 不把不可用解释为无缺陷/无回滚 |
| 路径或自由文本可作为 provenance | source trace/evidence 注入相对路径、secret-like value | fail-closed | 所有 provenance 只允许共享 privacy_ref 的 opaque ref |
| caller 可把 test fixture 标成 runtime/field | runtime/field receipt 不注入 verifier 或 verifier 返回 false | fail-closed | schema/opaque ref 只证明结构，来源信任由注入 verifier 提供 |
| hash 可替代来源 authority | receipt_id 绑定 canonical body 后直接声称 runtime | fail-closed 仍要求 verifier | hash 只证明完整性，不证明谁生成 |
| 未来观测可进入窗口 | 注入 2999 年 observed_at | fail-closed | measurement window 不接受未来数据 |
| abstain 会降低任务成功率 | 一条成功任务 + 一条正确 abstain | task/first-pass 分母为 1 且成功率 1.0；abstain precision 1.0 | abstain 不等于任务失败 |
| test/runtime 可声明 escaped defect | 在 test/runtime receipt 注入 escaped_defect | fail-closed | escaped defect 只允许 field；rollback 只允许 runtime/field |
| 任意 lambda True 可建立 runtime 信任 | canonical disabled policy + 已绑定 attestation + lambda True | fail-closed | registry 默认关闭；必须启用 managed backend 并命中 authority scope |
| attestation 可只绑定 authority ID | 篡改 attestation 的 manifest/bundle/layer/target/trace/body digest 任一项 | fail-closed | attestation 必须完整绑定 payload 与运行范围 |
| 陈旧或窗外 receipt 可进入聚合 | 2020 receipt、早于 aggregation from 的 receipt | fail-closed | 同时执行 max-age 与固定 window/as-of 门禁 |
| 1/2 可选字段可生成 0.0 | time/first-pass/escaped/rollback 只观测一半 | `not-measured/incomplete-coverage`，coverage=0.5，无 value | 部分覆盖不冒充完整测量 |
| mutable contract 可开启 production | test-only registry 改 `production=true` 并传 lambda True | contract/schema fail-closed；quality eligibility 始终 false | production authority 必须来自未来独立版本化 registry change |
| raw/sensitive receipt 可持久化 | raw=true、raw_prompt、Bearer-like value | fail-closed | schema、敏感字段和值模式三层拒绝 |
| 路由指标可互相矛盾 | routed 与 abstained 同为 true | fail-closed | 两者必须恰好一个为 true，outcome 同步 |
