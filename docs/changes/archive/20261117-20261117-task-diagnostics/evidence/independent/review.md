# 独立 Spec / Quality 审查：任务诊断

审查者：ai/independent-review（实际代理 /root/independent_review），AI、independent。C1 实现作者：ai/implement_diagnostics；协调者负责契约冻结、版本整合和证据包装。审查者未写产品代码、实施者测试或验收要求。

## 裁决与绑定范围

**Spec：PASS；Quality：PASS。** 无未解决 blocker/major。本裁决仅为 source-change，既有来源收集、发布、运行态、现场与效果资格不由本记录替代。

| 身份 | 已独立核实 |
|---|---|
| Base | 5f113b8f5ae6f83662d41d99d0907026f4e44c9d |
| 最终受测产品 Head | d01d1bcb7c2f322c342656a95e523fba8b55505e |
| 产品 Tree | 4fe0cfa656ad7feeabf1a25daa9012dcfd673ce0 |
| 完整原始 patch | 85,582 bytes；SHA-256 52fd79f40d5a6592d646c7897d5af605c32d88e6a3ade2c11e2ad41090affafe |
| 包装输入冻结 | 2026-11-17T15:12:48.626606Z；review-input-state SHA-256 02a5258c6dafb709ba9c4b7281364de3c60bd28da87a8f43cf452fe4b3cb17a0 |

最终产品与后续 change 证据包装分别审核。22 个变化产品文件均与 Git 中该 exact Head 逐字节相等；冻结输入清单的47份文件摘要和长度全部核实。包装 tracked delta 仅为本轮 change 的清单/任务/失败历史/生命周期状态及 C2 同字节归档位置说明，没有改写验收条件或产品。

本记录中的 change 内引用均相对 record，以允许正常 archive 移动。冻结输入状态和命令中的原路径属于原观察时的历史位置；后续 review/archive 可正常推进 lifecycle，不得把该快照重写为新状态。canonical 不直接把将来推进的 checklist/tasks/state/history/verify-report 绑定为永久产品不变量。

## Spec 判断

1. 显式 --diagnostics 是唯一启用条件。默认 importer/CLI 返回保持，诊断仅属于外层报告；Trace、RunEvidence、receipt、measurement、认证与 release 字段没有扩展。task_trials 默认调用不变。
2. 纯 Trace 投影先执行原 validator，复制原状态、原 unavailable reason、opaque 引用和对应 location；无额外日志内容读取。Importer 用同次已核验 ledger 的实际记录计数，不创建另一套事实源。
3. 未运行验收、失败后成功的 guardrail、实际零与 UNKNOWN 不被成功产物或后续状态覆盖。次数、attempt 与 wall time 不产生浪费、盲重试、并行等待或节省结论；真实模型效果仍 not-measured。
4. AAR 沿用原 Skill 的 References (only on demand)。压缩后 reference/template 均819 bytes且字节相等，旧 task: 开始的413-byte模板字段完整保留。输入包/ADK环境不存在时继续使用已有证据；详细界限保留在 runbook。
5. 11.4.0 为本次兼容新增 CLI 功能的版本；方法 fixture 只同步 planned_release，任务输入、固定期待与 grader 未改。无新 schema、Skill、Goal 权威、runtime、adapter、依赖、定时器或第三方源码。

## 独立证据

独立定向运行发生于前一产品 Head d0d2b2dc7cac3e7e7bb853bc372d4afc9975f6bd。Trace18、Task37、execution-policy25 与 target-contract脚本均实际 exit0；原冻结 C2 probe4/4通过。它们不是假称在最终 Head 重跑：独立 Git delta 证明最终 Head 仅修改两份 AAR 文本，Python、测试和预算字节未变；最终完整回归另外实际覆盖最终 Head。

独立 C1 probe 直接加载 Base 的原 task_evidence 模块，在相同包/依赖下做五组对照：普通成功、缺失 model coverage、未执行 acceptance、guardrail失败后成功、既有4096-event上限。每组的旧默认报告、候选默认报告和去掉diagnostics的报告都相等；finding指针逐个对应原Trace事实，修改诊断副本不改变原输入。4092次工具调用逐终态与独立Counter一致。queued/staged/deferred在旧、新默认、新diagnostics三路径均拒绝。

协调者在干净最终 worktree 实际执行完整102/102、exit0，2026-11-17T15:03:21.720367Z至15:09:48.688971Z，386.968613秒。Ruff、focused Ruff、mypy32源、format、strict、release check、core export均exit0；export为5agents/22skills。format保留既有脚本可执行位警告，不描述为零警告；release check明确runtime_eval_executed=false。

独立审核已重新核对两轮各1082个运行源输入：前后快照一致、实际工作树内容一致、覆盖全部按原规则选取的tracked输入，也覆盖全部22个产品变化文件。5个原始观察包共75份 observation 的 UTF-8原文、bytes、SHA和源文件逐一相等；C2七份冻结原始证据与先前scratch原件逐字节一致。该检查脚本及真实输出保存在本目录。

## 发现及处置

| ID | 严重性 / 处置 | 判断 |
|---|---|---|
| c1-footprint-ratchet | major / fixed | d0d2完整回归101/102，唯一footprint组失败：embedded318345>316854、large-refactor325227>323328。仅压缩重复AAR说明并同步模板；预算、测试、Python和入口均未改。最终full102/102。原失败保留。 |
| c1-footprint-headroom | minor / accepted-risk | 最终potential source为316356/323238，余量498/90 bytes。当前满足原门禁，未来增长仍由现有ratchet拒绝。该计量是源文件增长约束，不能换算runtime Token或收益。 |
| c1-checklist-label | minor / fixed | 首次lifecycle verify因在固定清单项追加解释被拒绝；说明移到正文，治理器未改，失败报告保留；两份当前verify实际通过。 |

初始新 API 缺失 RED、别名测试前提错误、reference/template不一致和首次full失败均保留，不用最终通过覆盖历史。较早一次独立定向工具输出丢失未作为证据；重新执行且完整观察结束的记录已留存。

## 限制与后续边界

诊断是 caller-observed/test-only；真实模型效果、成本/Token改善、宿主恢复、外部ACK/no-replay和native资格均未测量。知识Provider/实际宿主当前不可用；未另设authority或伪造宿主final gate。本次没有模型、设备、live安装或GitHub写入。

本裁决不认证随后远端CI、main合并、不可变Release或Root晋级；这些需各自exact-source真实回执。Source review的PASS也不把C1包含外部交付的TASK-003提前标为完成。回退需后继受保护源码变更，保留原始反例、版本与不可变发行历史。
