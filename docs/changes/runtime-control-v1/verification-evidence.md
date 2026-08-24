# Verification Evidence：runtime-control-v1

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tests/test_runtime_control.sh` | 0 | ADK Runtime Control 8/8 | `tests/test_runtime_control.py` | ADK targeted | R1-R8 |
| `rtk bash tests/run_all.sh --fail-fast` | 0 | ADK full 62/62 | `tests/run_all.sh` | ADK full | T2/T3 |
| `rtk python3 -m unittest tests.test_runtime_control tests.test_governance tests.test_check_script` | 0 | Codex targeted/governance 49/49 | `~/codex/tests/` | Codex targeted | T4/T5 |
| `rtk bash scripts/check.sh --no-build --plan build/apply-plan.json` | 0 | Codex 154 tests、五 profile smoke、live drift 0 | `~/codex/build/apply-plan.json` | Codex full/live | T8 |
| active path `rg` scan | 0 hits | old monitor/coach/ready/goal-template symbols absent | three repository active paths | Cross-repo | R9/R10 |
| `rtk bash scripts/check-adk-goal-capability.sh .` | 0 | root gate consumes single Runtime Control regression | `scripts/check-adk-goal-capability.sh` | llm_agent | T6 |
| no-network Python 3.11 wheel build | 0 | ADK 4.0.0 wheel SHA-256 `dd64702c2a405c34b08e5e07c4f5c09a04566ba72e6096bf6a0a8bb36b5a79a6` | `~/codex/vendor/wheels/agent_dev_kit-4.0.0-py3-none-any.whl` | Bundle | D8 |

| `rtk bash scripts/check-all.sh --quick --working-tree` | 1 | 50/55；Runtime/ADK/root 功能门禁通过，release 元数据 5 项未刷新 | root command output | llm_agent working tree | T8 |
| live active-path `rg` scan | 0 hits | old task/token/coach/ready symbols and empty directories absent | `~/.codex` managed paths | Runtime | R9/R10 |

Completion claim 保持 `needs-fix`：source-to-live 已完成，但 release-clean 必须在真实 ADK commit 后刷新 lock/current-status/M5/phase-gate，不能把 working-tree 证据冒充发布证据。
