# 负结果与修复边界

## 完整回归暴露两个不同问题

2026-10-21T01:27:42Z 至 01:33:18Z 的实际完整回归为 101 项、99 PASS、2 FAIL，退出码 1。原始回执与 stdout/stderr 保存在本目录 `evidence/`；文件名中的 `final` 是当时捕获目录名，不表示最终通过。

1. `test_harness_readiness`：版本同步使 README 字节改变，旧 `.adk/reviews/harness-source-20261020.json` 因来源摘要不符而失效。这是正确的来源门禁行为，必须对当前来源实际独立复审后新增记录；不得修改旧记录的哈希或日期。
2. `test_review_evidence`：实际 UTC 已是 2026-10-21，America/Los_Angeles 本地仍是 2026-10-20。生产入口用本地 `date.today()`，将 UTC 当天审核 metadata 误判为未来。测试没有硬编码昨天日期，也没有显式历史 `as_of`。

## 确定性复现与恢复

- 01:38:53Z 至 01:38:54Z 的旧实现回归：两个测试、三个失败子项、退出码 1。模拟 UTC 两侧的本地日期与真实 delegated Harness 链，保留具体失败原件。
- 修复仅把 Harness 入口默认日改为 `datetime.now(timezone.utc).date()`；原有显式 report-only 日期和 effective_as_of 传递不变。
- 01:39:22Z 至 01:39:24Z：全部 45 项审核证据测试通过，退出码 0。未来、过期、来源变化、scope、缺字段等原负例仍执行。
- 后续代码阅读发现 shell Harness 测试的两个本地日表达式也需要同步：当前日 fixture 在正 UTC 偏移区可能落到 UTC 明天；90 天陈旧预期可能差一天。独立 Quality 确认后只调整这两个测试日期表达式。

## 未采取的扩大修复

没有修改共享 `readiness_evidence.py` 的私有 fallback：实际生产入口已显式传入统一日期。修改该文件会改变所有 scope 的 validator 指纹并使无关归档审核失效。没有放宽未来/过期拒绝、审核独立性、policy/source/evidence 摘要或真实时间约束。

旧授权时间、旧审核、历史失败与产品资格状态均保持原样。新的 Harness 源码审核不构成 Native/provider 运行、G22 测量、LTA 现场事件或 Product M5 放行。

## 新记录的首次组装校验

02:01:32Z 的当前日 gate 实际退出 2，定向 Harness 脚本退出 1。直接调用既有 validator 定位为 `review finding identity is invalid or repeated`：作者组装新记录时直接沿用了审核原件中的大写 finding ID，但 canonical identity 只接受小写。将新 canonical record 的两项 ID 映射为小写，原始语义、严重性、已修复状态、来源绑定和 reviewer 原件保持不变。未修改 validator 或规避门禁。首次组装的 record 原字节、gate/定向输出与回执保存在 `evidence/assembly-red/`，不把它们报告为通过。
