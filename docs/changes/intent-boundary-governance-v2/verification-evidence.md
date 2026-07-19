# Verification Evidence：intent-boundary-governance-v2

## T1–T6 Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk python3 tools/check_manifest_sync.py` | 0 | JSON SSOT 与 YAML mirror 一致 | command output | Manifest | invocation SSOT |
| `rtk bash scripts/devkit.sh validate --quick` | 0 | quick manifest validation pass | command output | Product | T1 |
| `rtk bash scripts/check-official-docs-governance.sh --summary-json`（首次） | 1 | 发现 3 个 task Skill v2 marker 未同步 | `negative-results.md` | Manifest/Skill | T1/T3 negative |
| `rtk bash scripts/check-official-docs-governance.sh --summary-json`（修复后） | 0 | 69 sources、10 structured contracts、6 reproducibility contracts，failures=0 | command output | Manifest | T1/T4 |
| `rtk bash tests/test_intent_boundary_governance.sh`（首次） | 1 | residue gate 命中 active manifest 中旧 schema 字面量 | `negative-results.md` | Test | T1 negative |
| `rtk bash tests/test_intent_boundary_governance.sh`（修复后） | 0 | invocation mapping、v2 kind/permission、prototype evidence、hotspot scope 正负例 pass | command output | Product/Test | T1–T4 |
| `rtk bash tests/test_target_contracts.sh` | 0 | 三 direct target export/install contract pass | command output | Adapter | T2 |
| `rtk bash tests/test_skill_sop_quality.sh` | 0 | Skill SOP/asset strict quality pass | command output | Skill | T3 |
| `rtk bash tests/test_templates.sh` | 0 | 19/19 template checks pass | command output | Template | T3/T4 |
| `rtk bash tests/test_token_budget.sh` | 0 | max Skill 140 行，token budget pass | command output | Performance | T3 |
| `rtk bash scripts/devkit.sh validate --strict` | 0 | strict validation pass | command output | Product | T1–T4 |
| `rtk bash scripts/devkit.sh release check --summary-json`（首次） | 1 | `.version-lock` 未随 RC5 同步，fail closed | `negative-results.md` | Release | T5 negative |
| `rtk bash scripts/devkit.sh release check --summary-json`（修复后） | 0 | version=`3.1.0-rc.5`，failures=[] | command output | Release | T5 |
| `rtk bash tests/test_software_m5_ready.sh`（修复后） | 0 | RC5 M5-ready deterministic contracts pass | command output | Product | T5 |
| `rtk scripts/check-adoption-matrix-structured.sh .` | 0 | Markdown 与 JSONL adoption matrix 同步 | root command output | Provenance | T5 |
| `rtk scripts/check-adoption-matrix-status.sh .` | 0 | adopt/observe/reject 三类状态合法 | root command output | Provenance | T5 |
| `rtk scripts/check-doc-sync.sh .` | 0 | 根仓 docs/governance 同步 | root command output | Docs | T5 |
| `rtk scripts/check-adk-target-evidence.sh .` | 0 | checked=29，target evidence pass | root command output | Governance | T5 |
| Codex source residue scan | 0 | 63 files、63 nested、legacy=0、implicit-true=0、explicit-false=0 | `~/codex` command output | Runtime adapter | T6 |
| `rtk python3 -m unittest tests.test_check_skills` | 0 | 9/9，legacy/implicit-true/explicit-false/unknown policy 正负例 pass | `~/codex` command output | Test | T6 |
| `rtk bash scripts/check-skills.sh` | 0 | skills=63，errors=0，warnings=0 | `~/codex` command output | Governance | T6 |
| `rtk bash scripts/backup.sh --target ~/.codex` | 0 | apply 前备份完成 | `/home/leiwenjun/codex/.backups/codex-home/20260719-134739` | Rollback | T6 |
| Codex build/doctor/plan/dry-run | 0 | managed=712；doctor errors=0；overwrite=53、delete=0；dry-run pass | `~/codex/build/apply-plan.json` | Source-to-live | T6 |
| Codex apply/routing/live scan | 0 | apply pass；token-lean route pass；live 63/63 nested 且零 legacy/true | command output | Runtime | T6 |
| `rtk bash scripts/check.sh` | 0 | 99 tests、五 profile smoke、post-apply drift=0，最终 `[DONE] check` | command output | Full runtime | T6 |
| `rtk bash tests/run_all.sh --quick --timing-json .../quick-timing.json` | 0 | quick 18/18 | `quick-timing.json` | Test | T7 |
| `rtk bash tests/run_all.sh --timing-json .../full-timing.json`（首次） | 1 | 54/55；唯一失败为 change 文档外部仓名 | `negative-results.md` | Test | T7 negative |
| `rtk bash tests/run_all.sh --timing-json .../full-timing.json`（review fix 后） | 0 | 55/55 | `full-timing.json` | Test | T7 |
| `rtk bash scripts/devkit.sh security check --summary-json` | 0 | git inventory 727 files，0 failure，0 warning | command output | Security | T7 |
| `rtk bash scripts/devkit.sh benchmark run --iterations 10 ...` | 0 | 7/7 latency budgets 与 memory gate 全通过；I/O 10x p95=930.83ms，peak=276.7KiB | `benchmark.json` | Performance | T7 |
| `rtk bash scripts/check-performance-budgets.sh --strict --timing-json .../full-timing.json` | 0 | 3 项 full-suite budget pass | `full-timing.json` | Performance | T7 |
| independent review + re-review | 0 | blocker=0；2 major fixed；0 open minor | `review-findings.md` | Review | T7 |

## Checkpoint

- completed：T1–T6。
- current：T7 exact-commit deterministic release build/rehearsal、证据提交与复盘。
- open：implementation baseline commit、release rehearsal、evidence commit/Hub candidate。
- retry budget：未有同根因重复失败超过 1 次。
- stop condition：continue。
