# 需求：official-source-toolchain-refresh-20260830

## 目标

恢复 2026-08-30 已到期的 28 条 OpenAI 官方来源 freshness，并改善 ADK
Python 入口对已审查 3.11/3.12 解释器的可复现选择与诊断。

## 范围

- 逐条重新打开并复核 28 条来源，不允许仅延长日期。
- 更新 official freshness manifest、OpenAI reference inventory 和本 change 证据。
- Codex 来源先使用当日 Codex manual helper；其余来源使用 OpenAI Docs MCP，
  当前会话不可热加载 MCP 时仅回退到 OpenAI 官方域名。
- 允许调整 `scripts/devkit.sh`、Python launcher 定向测试及解释器说明。

## 硬边界

- 不修改 `manifest.json`、`manifest.yaml`、matcher 或 Runtime Control。
- 不把重定向后的产品文档、Cookbook 样例或 API 实现细节提升为平台绑定。
- 无法核验、URL 不可达或结论漂移未决时保持过期或降级为 `watch`，继续
  fail closed。
- 宿主旧 Python 的结果只作为 development evidence，不伪造 release evidence。

## 验收

1. 28 条来源均有 retrieved/review/expires、变更或无变更结论和来源边界记录。
2. 90 天 freshness 窗口、官方域名和 provider 最低数量门禁保持不变。
3. `validate --strict` 不再因本轮已核验来源到期失败。
4. Python launcher 选择顺序有确定性测试；显式 override 优先，unsupported
   Python 仍可诊断且严格模式 fail-fast。
5. 定向测试、official docs gate 和 diff 检查通过。

