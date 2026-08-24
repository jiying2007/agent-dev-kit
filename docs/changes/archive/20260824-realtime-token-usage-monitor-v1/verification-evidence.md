# Verification Evidence

## Scope

- typed core：`src/agent_dev_kit/token_monitor.py`。
- CLI：`devkit.sh token monitor`。
- tests/docs：Token monitor 定向测试、full runner、commands/runbook。
- llm_agent integration：`scripts/check-adk-goal-capability.sh` 与根仓合同测试。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk agent-dev-kit/tests/test_token_monitor.sh` | 0 | 8/8；阈值、速率/ETA、delta/snapshot、幂等、恢复、安全、file input、1000 events | `tests/test_token_monitor.py` | Skill/Test | R1-R8 |
| `rtk agent-dev-kit/scripts/check-format.sh` | 0 | format 和 executable mode 通过 | command output | Workflow/Test | T4/T5 |
| `rtk agent-dev-kit/tests/test_docs_cli_alignment.sh` | 0 | 新增 token 一级命令有完整 docs section | `docs/commands.md` | Workflow/Docs | T5 |
| `rtk agent-dev-kit/tests/test_scripts_smoke.sh` | 0 | 25/25；token monitor help smoke 通过 | `tests/test_scripts_smoke.sh` | Workflow/Test | T5 |
| `rtk agent-dev-kit/scripts/run-local-ci-parity.sh --python 3.11 --mode quick` | 0 | isolated Python 3.11；22/22、strict、targets、routing 30/30、wheel、dependency audit | tool transcript | Workflow/Test | supported quick |
| `rtk agent-dev-kit/scripts/run-local-ci-parity.sh --python 3.11 --mode full` | 0 | isolated Python 3.11；60/60、strict、targets、routing 30/30、wheel、dependency audit | tool transcript | Workflow/Test | supported full |
| `rtk scripts/check-doc-sync.sh .` | 0 | 根仓 docs/governance 同步 | command output | Workflow/Root | llm_agent |
| `rtk scripts/check-agents-coverage.sh .` | 0 | active=8，missing=0 | command output | Workflow/Root | llm_agent |
| `rtk scripts/check-token-budget.sh . --summary-json` | 0 | cumulative AGENTS 9425/12000，warnings=0，failures=0 | command output | Workflow/Root | token budget |
| `rtk tests/test_adk_goal_capability_contract.sh` | 0 | 根仓目标 gate 覆盖 realtime monitor | root test | Workflow/Root | llm_agent integration |
| `rtk scripts/check-adk-goal-capability.sh .` | 0 | goal/capability/realtime monitor/benchmark 通过 | command output | Workflow/Root | llm_agent integration |

## Negative / Disproved Paths

- before：`token` 命令不存在，6/6 新测试失败；见 `negative-results.md`。
- 同 scope 混用 delta/snapshot 会双计，已改为 fail closed。
- 初轮 self-review 的四个 major（失败计数、持久化顺序、`~` path、state consistency）均已修复并复审。
- 宿主香港日期与 UTC CI 日期不同导致 official freshness gate 结论不一致；这是独立治理缺口，
  不通过延长 expiry 掩盖，后续 change 单独修复。

## Replayable Evidence Bundle

- input_snapshot：`before-after.json` 与 `tests/test_token_monitor.py` fixtures。
- environment_snapshot：Python 3.11.15 isolated Docker；source read-only、tmpfs copy、gate network none、
  fixed non-root user、credentials not mounted。
- tool_transcript_digest：quick/full parity 分别记录 source snapshot、definition hash、image ID 和 wheel hash。
- expected_assertions：8 个 deterministic unittest + 60 个 full regression。
- sensitive_data_review：事件只允许计数、bounded identifiers、time/provider/model；正文键与未知键拒绝。
- non_replayable_reason：真实 provider/runtime adapter pilot 未执行；不以 fixture 推断真实集成效果。

## Completion Guard Payload

| Check | Status | Exit | Evidence | Verifier |
|---|---|---:|---|---|
| build/install | pass | 0 | Python 3.11 wheel build/install in quick/full parity | isolated runner |
| format | pass | 0 | `check-format.sh` | deterministic gate |
| targeted test | pass | 0 | 8/8 | unittest |
| full regression | pass | 0 | 60/60 | isolated runner |
| security/privacy | pass | 0 | sensitive/unknown field negative tests + no credentials mounted | deterministic gate |
| root integration | pass | 0 | goal capability + contract test | deterministic gate |
| independent semantic review | not-run | - | only author-self-review available | owner/fresh reviewer required |

## Final Integration

- Python 3.11 full parity final source snapshot：`268dc95b09fabf92105c05fe957222a5de3bb3f14b4c4cffad7f1e8357ed12d0`。
- 63/63 full regression；routing 30/30；wheel/install、strict、targets、dependency audit pass。

- completion_allowed：false，直到独立/owner semantic review 与 change review gate 完成；实现与机械验证已闭环。
- breaking_change：false；新增命令，旧 CLI/manifest/runtime 行为不变。
- rollback：删除新增 module/command/test/docs/root gate 行；无数据库或 live runtime migration。
