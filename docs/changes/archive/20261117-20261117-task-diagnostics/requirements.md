# 需求：按需诊断已验证任务证据

## 目标与授权

用户在 LoopForge 与同类方案审查后明确要求“按建议全部优化落地完成”。本变更只吸收事实优先、按需复盘这一增量，沿用 ADK 的 Trace v2、RunEvidence 与任务包导入边界。基线为 11.3.15，提交 `5f113b8f5ae6f83662d41d99d0907026f4e44c9d`。

## 验收

- REQ-001 / ACC-001：`eval import-task --diagnostics` 显式请求才向现有外层报告增加诊断；无参数报告及 RunEvidence、receipt、measurement、资格值不变。有效失败任务仍可成功导入；无效包仍脱敏拒绝。
- REQ-002 / ACC-002：诊断只展示同次核验的事实、原状态、opaque evidence ref 和缺测原因。保留全部失败、未运行项、真实尝试数及工具终态计数；合法零值与 unavailable 区分。不得由调用数推断浪费、盲重试，由墙钟推断并行等待或节省。
- REQ-003 / ACC-003：纯 Trace 投影可重复且不修改输入；task importer 复用已验证账本，不能新增读取或绕过输出别名保护。Trace 汇总中的 partial 不伪造精确失败次数。
- REQ-004 / ACC-004：既有 AAR Skill 通过按需引用说明诊断用法、来源和限制，不增加默认提示预算、不新增 Skill。静态方法检查不冒充模型效果测量。
- REQ-005 / ACC-005：兼容功能按 11.4.0 统一版本；完整源码回归、独立 Spec/Quality、受保护 CI、不可变发行和 Root source-only 晋级分别以实际回执验收，不提前授予产品资格。

## 必须保留的反例

50 次同工具成功调用无浪费判断；混合成功/失败保留 partial 和准确终态计数；多个 attempt 最终成功不推断盲重试；仅 first_pass_success=false 不虚构 attempt 数；产物通过不能覆盖过程失败；同名 guardrail 先失败后通过仍保留失败；验收 not-run 无终止事实时 outcome unavailable；明确 timeout 时保留 failed/runtime-timeout 和 not-run；缺失或估计计量保持原 unavailable reason；合法实测零值；多个 handoff 和 1000 ms 墙钟不推断并行收益；无 flag 原行为；重复投影稳定且输入不变；无效包和输出输入别名仍拒绝。

## 非目标与资格

不新增 schema、runtime、调度器、Goal、MCP、定时任务、每日预算、价格估算或模型调用；不复制第三方代码。保持 caller-observed、test-only、quality_evidence_eligible=false、release_authorized=false。宿主原生恢复和真实效果测量需实际宿主证据，不能由本变更获得。
