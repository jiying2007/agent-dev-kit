# Verification Evidence

当前状态：`verified-working-tree`。实现与 source-to-live 已通过；当前 dirty 状态不等于 release-clean。

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk tests/test_task_cost.sh` | 0 | task cost 正负合同通过 | command output | ADK | R2 |
| `rtk tests/test_token_budget.sh` | 0 | soft/hard budget 字段通过 | command output | ADK | R1 |
| `rtk scripts/check-token-budget.sh . --summary-json` | 0 | cumulative 9425 bytes / est. 2357 tokens / warnings 0 | command output | root | R1 |
| `rtk tests/test_check_all_contract.sh` | 0 | 双模式与 fingerprint contract 通过 | command output | root | R3/R6 |
| `rtk tests/test_current_status_consistency.sh` | 0 | release dirty fail / working-tree pass | command output | root | R3 |
| `rtk tests/test_same_run_evidence.sh` | 0 | 同轮证据复用正负合同通过 | command output | root | R6 |
| `rtk scripts/check-all.sh --smoke --working-tree --result-json /tmp/llm-agent-v2-smoke.json` | 0 | 13/13，真实 reuse 7 | `/tmp/llm-agent-v2-smoke.json` | root | R3/R6 |
| `rtk python3 -m unittest tests.test_apply_prune tests.test_skill_catalog tests.test_governance_summary tests.test_usage_dashboard tests.test_check_script` | 0 | Codex 26 tests passed | command output | Codex | R4/R5 |
| `rtk python3 -m tools.codex_assets governance-report --root . --summary-json` | 0 | governance pass | command output | Codex | R5 |
| `rtk python3 -m pytest -q tests/test_context.py tests/test_lifecycle.py tests/test_review_queue_sla.py` | 0 | Hub 26 tests passed | command output | Hub | R7/R8 |
| `rtk tests/test_cross_repo_release_bundle.sh` | 0 | 四仓 fingerprint/plan/candidate/evidence provenance contract 通过 | command output | root | R9 |
| `rtk scripts/run-local-ci-parity.sh --mode quick` | 0 | Python 3.11.15/3.12.13 各 20/20 tests、30/30 routing、wheel/target/audit 通过 | Docker isolated runtime output | ADK | R2/T6 |
| `rtk tools/ci/python-runtime.sh -m pytest -q` | 0 | Hub full pytest 通过（锁定 Python 3.14） | command output | Hub | R7/R8 |
| `rtk bash tools/knowledge-check.sh --dry-run --summary-json` | 0 | Hub check status=pass、errors=0、warnings=0 | command output | Hub | R7/R8 |
| `rtk scripts/check-all.sh --full --working-tree --result-json /tmp/llm-agent-v2-full-final.json` | 0 | 61/61，reuse=13，fingerprint stability pass | `/tmp/llm-agent-v2-full-final.json` | root | R3/R6/T6 |
| Codex build/doctor/plan v3/apply dry-run/apply/check | 0 | live 2 文件更新；repeat plan=already-applied；live diff=0 | `~/codex/build/apply-plan.json` | Codex/runtime | R4/R5/T7 |
| Hub capture apply | 0 | reviewing candidate 已事务写入，未 promotion | `projects/agent-dev-kit/validation/2026-08-01-token-context-governance-v2.md` | Hub | T7 |
| cross-repo bundle | 0 | 四仓 HEAD/dirty fingerprint、plan/candidate/evidence hashes；release_authorized=false | `reports/2026-08-01-token-context-governance-v2-release-bundle.json` | root | R9/T7 |
