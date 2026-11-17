# 当前源码验证与交付边界

## 输入与实现

基线 `5f113b8f5ae6f83662d41d99d0907026f4e44c9d`（11.3.15）；最终产品候选 `d01d1bcb7c2f322c342656a95e523fba8b55505e`（11.4.0）。实现者 `implement_diagnostics` 负责 C1，`audit_core` 负责 C2；coordinator 冻结契约及整合，`independent_review` 对 ADK 保持只读审核。

Root 来源范围和独立 owner 决策已由 PR #347 合入 `761e41b28b93b6b3fb5b8c451870afb0c45e0c5a`，canonical 材料为 `docs/changes/20261117-loopforge-adoption/`。仅 LoopForge 为 ENHANCE，其余6源 OBSERVE；不复制第三方源码或 Prompt、不新增控制面。

## 验收映射

| 验证 | 已实际获得的证据 |
|---|---|
| VERIFY-001：显式 opt-in 与默认兼容 | 实现者 Trace18/Task37；独立原 baseline importer 五组对照，包括4096 events，默认报告逐对象相等 |
| VERIFY-002：失败、未知与计数无损 | 精确终态、多attempt、合法零/缺测、timeout/not-run、guardrail失败优先等原始定向日志 |
| VERIFY-003：读取/写入安全与纯投影 | 相同读取集合、no-follow/摘要/输出别名保护；纯输入不变；queued/staged/deferred三路径拒绝 |
| VERIFY-004：既有 AAR 按需说明 | content211/SOP22/Profile6；reference与模板同为819 bytes、原413-byte模板字段保持 |
| VERIFY-005：版本及本地源码门 | 最终洁净候选完整回归102/102、exit0；strict、Ruff、mypy32、format、release check及core export通过；原始输入与日志见evidence/final/，远端CI/Release/Root晋级以对应真实回执续行 |

最终完整回归实际开始于2026-11-17T15:03:21.720367Z、结束于15:09:48.688971Z，用时386.968613秒。候选tree为`4fe0cfa656ad7feeabf1a25daa9012dcfd673ce0`；1082个运行源输入前后完全一致。core claude-code export实际导出5个agents与22个skills。此后只补充change证据包装，产品源码不得变化；独立review分别绑定测试候选和包装输入。

## 真实失败和修订

`d0d2b2d` 洁净完整回归为101/102，唯一失败为 Profile source footprint；1082 个运行源输入前后字节一致。该轮原始日志、退出码、时序、源快照和失败汇总位于 `evidence/full-attempt1/`，没有被覆盖。只压缩重复 AAR reference，并同步原模板；Python、测试、预算、权限和入口保持。最终两个受影响 Profile potential source 分别316356/323238 bytes，原上限316854/323328不变。源码字节不换算实际运行Token或费用收益。

初始未实现 API 的 RED、别名测试前提错误、reference/template同步拒绝均在 negative-results.md 和 `evidence/implementation-observations.json` 保留；修订没有弱化原断言、扫描或测试。

## 资格与续行

本地 CPython3.12.14，仅真实确定性源码/工具测试。task import 保持 caller-observed、test-only、quality_evidence_eligible=false、release_authorized=false；没有模型A/B、真实宿主加载、设备或现场运行。synthetic verifier 反例只证明 reducer 历史消费缺口，不能证明实际宿主授权曾被绕过。

实际知识入口调用退出127，`/home/agent/codex/scripts/knowledge-provider.sh` 不存在；宿主工作目录缺失。Provider/宿主 Execution Policy 为 UNAVAILABLE/NEEDS_REVIEW，不创建替代 authority、不伪造知识入库或 host final gate。

源码 review/archive 仅封存该源码范围的独立裁决；不预填外部合并、不可变发行或 Root晋级结果。用户已明确授权受保护推送、审核和合并，后续分别核 exact PR/main CI、immutable Release及其来源签名，再走 Root source-only 事务；未执行的运行态和资格保持未执行。

回退：默认调用未启用diagnostics；可直接移除该显式flag恢复原输出。已发布源若需回退，应以正常后继受保护变更恢复旧pin或修复，不移动既有tag、覆盖发行资产或改写历史证据。
