# ADK 3.0 Verification Report

- version: 3.0.0
- environment: Linux, Python 3.8.10
- evidence_state: verified-local
- field_status: field_not_verified

## Contract Evidence

| Area | Command | Result |
|---|---|---|
| Manifest | `rtk bash scripts/devkit.sh validate --strict --summary-json` | PASS; 12 agents, 56 core skills, 9 optional skills, 9 profiles, 6 workflows |
| Product contract | `rtk bash tests/test_product_maturity_v3.sh` | PASS; manifest, install, rollback, release, security and eval negative paths covered |
| Security | `rtk bash scripts/devkit.sh security check --summary-json` | PASS; no failure or warning |
| Release readiness | `rtk bash scripts/devkit.sh release check --summary-json` | PASS; direct targets are Claude Code, Hermes Agent and OpenCode; Codex remains external handoff |
| Deterministic eval | `rtk bash scripts/devkit.sh eval run --suite deterministic` | PASS; 30/30 |
| Full regression | `rtk bash tests/run_all.sh --timing-json docs/changes/adk-v3-product-maturity/full-regression.json` | PASS; 48/48, 0 failures, 395482 ms |
| Performance | `rtk bash scripts/devkit.sh benchmark run --iterations 10` | PASS; validate/resolve/export P95 = 54.157/5.811/11.360 ms, within 200/50/100 ms budgets |

## Runtime Evaluation

The initial Codex run recorded baseline `23/30` and ADK `27/30`. That run exposed an underspecified shared safety policy, so it is retained as diagnostic evidence rather than the final comparison. The final comparison uses the same explicit approval policy for both conditions: baseline passed `27/30` with success/route/safety `0.90/0.90/1.00`; ADK passed `30/30` with `1.00/1.00/1.00`. `codex-comparison-final.json` passes the candidate gate with success and route deltas of `+0.10` and no safety regression.

Latency is observational rather than gating. Baseline total/median/P95 was `428948.440/13586.498/16920.324 ms`; ADK was `417341.769/13343.642/18256.005 ms`. Total and median decreased, while P95 increased by `1335.681 ms`; one fixed-suite run is insufficient for a statistically defensible latency claim.

Claude CLI is installed but `claude auth status` reports `loggedIn=false`. Claude baseline/adk execution is therefore `not-run`; no result is inferred or fabricated.

## Release And Rollback

The product contract verifies two byte-identical release archives, SHA256 sidecars, SPDX 2.3 dependency metadata, source distribution contents, explicit publish backend selection and checksum rejection. The final source-snapshot checksum is deliberately recorded in the root delivery evidence outside the archive to avoid a self-referential checksum. Source assembly rejects symlinks and excludes Python build residue. Install coverage includes unmanaged conflicts, plan tampering, managed drift, rollback preflight, injected I/O failure, nested replacement and restoration of the previous receipt.

The isolated package build produced `agent_dev_kit-3.0.0-py3-none-any.whl` with SHA256 `f0b9b837a7eb3a42e4629daa166787a46190dac2e07f9b640855c654b31e9fb0`. Installing the wheel resolved its declared PyYAML dependency; the console script then passed `pip check`, ran the evidence-validating `eval compare` without a checkout and validated the checkout from `/tmp` through explicit `ADK_ROOT`.

## Review Closure

| ID | Severity | Finding | Resolution | Re-review evidence |
|---|---|---|---|---|
| R1 | major | Source distribution could include local `*.egg-info` after wheel builds | Ignore build metadata in Git and release assembly; reject source symlinks | product contract release inventory + reproducible build |
| R2 | major | `export --clean` deleted the previous export before replacement succeeded | Move the previous tree to staging and restore it on replacement failure | injected second-rename failure preserves marker |
| R3 | major | Runtime comparison trusted mutable summary metrics | Recompute per-task metrics, gates and status; reject duplicate IDs, wrong conditions and tampered summaries | tampered candidate summary is rejected |
| R4 | minor | Intake archive loaded all member metadata before enforcing the member cap | Iterate and cap tar members incrementally | root reference-source integrity test |

Re-review verdict is `pass`: blocker `0`, unresolved major `0`. AI-assisted review remains subject to repository-owner review for protected-branch or release decisions.

## Evidence Index

| Command | Exit | Result | Evidence | Layer |
|---|---:|---|---|---|
| `rtk bash tests/run_all.sh --timing-json ...` | 0 | 48/48 | `full-regression.json` | test |
| `rtk bash tests/test_product_maturity_v3.sh` | 0 | product and negative contracts pass | `tests/test_product_maturity_v3.sh` | test |
| `rtk bash scripts/devkit.sh security check --summary-json` | 0 | no failures or warnings | security JSON output | test/runtime |
| `rtk bash scripts/devkit.sh release check --summary-json` | 0 | 3 direct targets, Codex external | release JSON output | test/runtime |
| `rtk bash scripts/devkit.sh eval compare ...` | 0 | `0.90 -> 1.00`, no safety regression | `codex-comparison-final.json` | runtime |
| initial Codex A/B with underspecified policy | diagnostic | 23/30 and 27/30 retained | `codex-baseline-full.json`, `codex-adk-full.json` | negative/runtime |

## Residual Boundaries

- Claude CLI is not authenticated, so its 30-task baseline and ADK plans remain `not-run` rather than inferred results.
- The runtime comparison is one explicit-keyword, fixed 30-task suite without repeated trials, confidence intervals or open-world coverage; it demonstrates a representative local gain, not universal model behavior.
- Concurrent writers against the same export/install target have not been stress-tested; operational use assumes one approved writer per target and relies on conflict/drift checks rather than a distributed lock.
- Real hardware, long-duration operation, multi-team adoption, production rollback and field telemetry remain outside this software-only verification. Product maturity therefore remains `field_not_verified` and must not be promoted to terminal maturity from this report.
