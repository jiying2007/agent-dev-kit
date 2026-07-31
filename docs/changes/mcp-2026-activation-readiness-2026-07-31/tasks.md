# 任务：mcp-2026-activation-readiness-2026-07-31

| Task | Status | Scope Write | Must Not Touch | Verify |
|---|---|---|---|---|
| T0 checkpoint | completed | proposal/design/tasks/checklist/state/preflight | runtime、owner ledger | change governance |
| T1 red-fixture | completed | Go fixture、wrapper | manifest completed/claim 字段 | 专用测试因 readiness pending 红灯 |
| T2 pinned-prepare | completed | `go.sum`、`/tmp` module cache | repo vendor/lockfile、用户 cache | module version/sum/image digest |
| T3 four-smokes | completed | fixture 实现、negative results | 真实服务/credential | schema/client-server/auth/rollback 分项绿灯 |
| T4 readiness-state | completed | manifest/checker/test/evidence | active/runtime/features/owner decision | ecosystem + offline smoke |
| T5 full-verification | completed | verify/review/state | commit/push/source-to-live | strict + full + final-ready |
| T6 owner-decision-request | completed | 独立 decision request/decision contract | 代签 owner 结论 | request + schema + evidence links |
| T7 activation-closeout | completed | 仅 owner 决策授权的状态 | Tasks/Apps/extensions、无关资产 | ACTIVATE record + scoped state + gates |

## Ownership 与并行冲突检查

- owner：`leiwenjun`
- claimant/implementer：Codex 当前会话。
- independent verifier：机械化 Go/manifest/ADK gates；owner activation decision 已由
  `leiwenjun` 独立签署。
- scope_read：MCP final source、Go SDK `v1.7.0-pre.3` API、现有 MCP manifests/checker/tests。
- scope_write：本 change、MCP fixture/wrapper、MCP manifest/checker/test、对应根仓 evidence/
  decision request。
- must_not_touch：其他 dirty 变更、active protocol、target runtime、credential、安装目录。
- 本任务串行执行，不使用子代理。

## Retry、heartbeat 与停止条件

- 每个 smoke 最多修正 2 轮；连续失败后把原始输出写入 `negative-results.md` 并重审假设。
- 每完成一个 smoke 更新 `state.yaml` heartbeat 和 tasks 状态。
- source/package evidence 超过 1 天需在 owner decision 前刷新。
- stop condition：
  - `ready-for-owner-decision`：四项通过且 full gates 可解释；
  - `replan`：固定 SDK 行为与 final contract 不符；
  - `blocked`：依赖不可取回或 owner 尚未决策。

## 轻量工件与收敛结论

- 轻量工件：proposal/design/tasks/checklist/state/negative-results。
- 已补充 verify-report、review-report、独立 owner decision request 与 Knowledge Hub
  validation candidate。
- 当前收敛结论：owner 已选择 `ACTIVATE`，只激活 protocol governance contract；
  runtime、Tasks、Apps、extensions 保持关闭。
