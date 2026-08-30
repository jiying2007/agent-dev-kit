# 需求：effect-comparator-v1

## 目标

在不伪造 native/runtime/field evidence 的前提下，为相同任务集的 baseline 与 ADK candidate 提供可重算、
coverage-aware 的本地效果对比。

## 要求

1. 输入只接受 validated Run Evidence composition。
2. task population 必须非空、唯一、完整覆盖并输出 count/digest。
3. baseline/candidate 不得复用 run，必须绑定不同 asset bundle。
4. 对应任务必须使用相同 runtime target/version/model；不隐式混合环境。
5. 固定 campaign window；future 或窗口外 run 拒绝。
6. outcome/cost/token 缺失时不补零、不对子集输出 measured average。
7. currency 不一致时 cost comparison 拒绝。
8. 输出永远 test-only、quality ineligible、无 lifecycle authority。
9. 不持久化、不联网、不启动 runtime、不生成 owner decision。

## 非目标

- 不证明 task population 代表生产分布。
- 不替代 native target conformance、R10 campaign 或 Software M5 certifier。
