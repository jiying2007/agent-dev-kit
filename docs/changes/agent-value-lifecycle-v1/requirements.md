# 需求：agent-value-lifecycle-v1

## 目标

落实 `adk-platform-convergence-v1` 的 R8 与根仓 G22 第一阶段：为 manifest 中的全部 Agent 建立
typed role/value contract，并为 Agent、Skill、Profile 建立脱敏 invocation receipt 与价值退役信号合同。

## 范围

- 新增独立的 Agent value contract、JSON Schema 和 typed validator。
- Agent/Skill/Profile 的身份与成员关系继续以 `manifest.json` 为 SSOT；价值合同只保存资产 ID 引用和治理语义。
- 新增正例、负例、边界测试并接入 `tests/run_all.sh`。
- 新增操作 runbook；不修改 manifest、matcher、trace、runtime、target 或 official-docs checker。

## 验收标准

1. typed validator 必须从 manifest 动态解析 13 个 Agent、全部 core/optional Skill 和全部 Profile。
2. 每个 Agent 必须声明 role input/output、permission envelope、decision authority、handoff、required
   evidence、assumption scope 和 eval suite。
3. Agent 合同必须完整覆盖 manifest Agent，不能增加未知 Agent；权限 profile/effect/tool capability 不能高于
   manifest 声明的 permission ceiling；handoff 只能引用 manifest 已声明的有效 Agent。
4. invocation receipt 必须包含 asset ID/kind、routed/abstained/wrong-route、outcome、human
   interventions、retirement signal、privacy status，并固定 `raw_content_stored=false`。
5. receipt 必须解析到当前 manifest 的 Agent/Skill/Profile；敏感字段、raw content、错误指标类型和矛盾路由状态
   fail-closed。
6. Asset 数量、invocation/PR/report 数量和 Token 总量只能作为诊断量，不能进入 quality KPI。
7. emitter 默认保持 `status=not-measured`、`runtime_enabled=false`；只有显式输入至少一条 schema-valid、manifest-resolved、脱敏 receipt 时，才可输出 `measured` 聚合结果。
8. 每个质量指标必须显式区分 `measured` 与 `not-measured`；字段未观测或无适用 receipt 时不得以 `0` 代替未知。
9. test/runtime/field evidence layer 必须分组聚合；receipt、invocation、source trace 与 evidence 只允许 `ref:<sha256>` opaque reference。
10. receipt ID 与同资产 invocation observation 必须去重；非法状态、伪 measured 声明、raw path/secret reference 必须 fail-closed。
11. runtime/field receipt 必须通过调用方注入的 evidence verifier；默认无 verifier 时拒绝。test receipt 只构成 structural/test evidence。
12. `receipt_id` 必须绑定 canonical receipt body；hash 只证明内容完整性，不授予来源 authority。
13. `observed_at` 不得晚于验证时钟；measured output 必须给出 observation window 的 `from/through`。
14. canonical authority policy 默认 disabled/no authorities；runtime/field 必须同时满足 managed registry、scope-bound attestation 与 external verifier。
15. receipt 必须绑定当前 manifest、asset bundle、runtime target，并落入固定 aggregation window/as-of 与 `max_age_days`。
16. 可选 KPI 必须报告 applicable/observed sample size 和 coverage；first-pass/time/escaped/rollback 非完整覆盖时不得 measured。
17. 顶层 evidence scope 必须区分 test-only/runtime-verified/field-verified/mixed；v1 的 quality evidence eligibility 对全部 scope 固定 false，任何结果仍需 owner review 且无 lifecycle authority。
18. authority registry 输入在 v1 只允许 `production=false`；production authority 必须等待独立、版本化 managed registry change，不能由 input contract 或 callback 开启。

## 非目标

- 不实现 runtime 自动采集器、后台 scheduler、外部写入或 retirement 自动执行；本 emitter 只消费调用方显式提供的受验证 receipt。
- 不把 content hash 或 opaque ref 当作 runtime/field source attestation；trust 只能由显式 evidence verifier 提供。
- 不把测试构造的 receipt 宣称为 runtime/field usage evidence。
- 不修改任何现有身份、权限或 Profile 组成。

## 回滚

删除本 change 新增的 manifest/schema/module/test/runbook，并从 `tests/run_all.sh` 移除单行测试入口即可；
现有 manifest、runtime 与导出行为不受影响。
