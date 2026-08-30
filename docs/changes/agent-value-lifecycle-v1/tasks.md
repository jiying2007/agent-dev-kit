# 任务：agent-value-lifecycle-v1

- [x] T1 冻结 R8/G22 第一阶段目标、写范围、权限与 usage 真实性边界。
- [x] T2 新增 Agent value contract 与两个 Draft 2020-12 Schema。
- [x] T3 实现 typed contract/receipt validator 和只读 CLI。
- [x] T4 新增正负测试并接入 quick/full `run_all`。
- [x] T5 补 runbook、定向/quick 验证和交叉复核交接证据。
- [x] T6 实现 explicit-receipt measured emitter、opaque refs、evidence-layer 隔离与 no-zero 状态语义。
- [x] T7 增加真实性、隐私、重复 observation、不可用指标和状态矛盾负例。
- [x] T8 关闭独立预审 major：trust verifier、canonical body binding、future guard/window、KPI denominator 与 evidence-layer applicability。
- [x] T9 关闭终审：managed authority registry/attestation、manifest/bundle/runtime binding、max-age/window、coverage completeness 与 evidence scope。

## 执行控制

- retry budget：同类失败 2 次后先更新假设，不重复盲修。
- staleness threshold：验证证据只接受本 change 完成后的当前工作树输出。
- stop condition：定向测试通过后进入 quick 回归；共享冲突或越界写入时立即 replan。
- completion claim：合同、validator、正负测试和 runbook 均存在且当前证据通过。
- verifier：父 Agent/独立 subagent 交叉验证；本 Agent 先做范围与回归自检。
