# Verification Evidence：intent-boundary-governance-v2

## T1–T7 Evidence Index

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
| `rtk python3 -m unittest tests.test_check_skills` | 0 | 11/11，legacy/implicit-true/explicit-false/unknown policy 与官方 optional fields 正负例 pass | `~/codex` command output | Test | T6 |
| exact-index `rtk python3 -m unittest tests.test_openai_metadata_contract` | 0 | 精确 Codex 暂存树 5/5，通过且未夹带既存 dirty | `/tmp/codex-index-verify.MzMgsA` command output | Test/Commit | T6/T7 |
| `rtk bash scripts/check-skills.sh` | 0 | skills=63，errors=0，warnings=0 | `~/codex` command output | Governance | T6 |
| `rtk bash scripts/backup.sh --target ~/.codex` | 0 | apply 前备份完成 | `/home/leiwenjun/codex/.backups/codex-home/20260719-134739` | Rollback | T6 |
| Codex build/doctor/plan/dry-run | 0 | managed=712；doctor errors=0；overwrite=53、delete=0；dry-run pass | `~/codex/build/apply-plan.json` | Source-to-live | T6 |
| Codex apply/routing/live scan | 0 | apply pass；token-lean route pass；live 63/63 nested 且零 legacy/true | command output | Runtime | T6 |
| `rtk bash scripts/check.sh`（最终） | 0 | 101 tests、五 profile smoke、governance/sandbox/routing 与 post-apply drift=0，最终 `[DONE] check` | command output | Full runtime | T6/T7 |
| Codex final source-to-live plan/dry-run/apply | 0 | copy=0、overwrite=0、delete=0；keep=440，运行态已收敛 | `~/codex/build/apply-plan.json` | Source-to-live | T6/T7 |
| Codex live metadata residue scan | 0 | files=63、nested=63、legacy=0、implicit-true=0、explicit-false=0 | command output | Runtime | T6/T7 |
| Codex exact staged-tree check | 0 | skills=61、errors=0、warnings=0；legacy/implicit-true 零命中 | `/tmp/codex-index-verify.MzMgsA` | Commit isolation | T7 |
| `rtk bash tests/run_all.sh --quick --timing-json .../quick-timing.json` | 0 | quick 18/18 | `quick-timing.json` | Test | T7 |
| `rtk bash tests/run_all.sh --timing-json .../full-timing.json`（首次） | 1 | 54/55；唯一失败为 change 文档外部仓名 | `negative-results.md` | Test | T7 negative |
| `rtk bash tests/run_all.sh --timing-json .../full-timing.json`（review fix 后） | 0 | 55/55 | `full-timing.json` | Test | T7 |
| `rtk bash scripts/devkit.sh test --timing-json .../full-test-timing.json`（归档门禁修复后） | 0 | 55/55 | `full-test-timing.json` | Test | T7 |
| `rtk bash scripts/devkit.sh security check --summary-json`（最终） | 0 | git inventory 731 files，0 failure，0 warning | command output | Security | T7 |
| `rtk bash scripts/devkit.sh benchmark run --iterations 10 ...` | 0 | 7/7 latency budgets 与 memory gate 全通过；I/O 10x p95=930.83ms，peak=276.7KiB | `benchmark.json` | Performance | T7 |
| `rtk bash scripts/check-performance-budgets.sh --strict --timing-json .../full-timing.json` | 0 | 3 项 full-suite budget pass | `full-timing.json` | Performance | T7 |
| `rtk bash scripts/check-change-governance.sh ...`（首次） | 1 | 定制工件缺等价章节且完成态 checkbox 被误拒绝 | `negative-results.md` | Workflow | T7 negative |
| `rtk bash tests/test_change_governance.sh`（修复后） | 0 | `[ ]|[x]` 均可验证，标签改名 fail closed | command output | Workflow/Test | T7 |
| `rtk bash tests/test_workflow.sh`、`tests/test_integration.sh` | 0 | workflow lifecycle pass；integration 8/8 | command output | Workflow/Test | T7 |
| ADK implementation/release commits | 0 | `6d56834` contract hard-cut；`109049c` release boundary；`0fe2d4e` completed-checklist archive gate；`66a8c19` 受管归档与 release source | git history | Commit | T7 |
| Codex source commit | 0 | `684f7f8` 精确提交 50 metadata、checker 本次 hunks 与 5 tests | Codex git history | Commit | T6/T7 |
| RC5 exact-commit deterministic build A/B | 0 | release source commit=`66a8c19`；两份 611-file artifact 字节一致，SHA256=`7c0ddf0c0d0e2174abcb682e0df1e6b5d10fdcb8695bdaaa2dccc37a5daf3907`，checksum 均通过 | `/tmp/adk-rc5-release.zxGIZu/candidate-g|candidate-h` | Release | T7 |
| RC4→RC5 `release rehearse`（最终） | 0 | `target-contract-hard-cut`、rollback-before-install、candidate rollback、RC4 62-asset fallback restore 全 pass | `release-rehearsal.json` | Release | T7 |
| independent review + re-review | 0 | blocker=0；3 major fixed；0 open minor；verdict=pass | `review-findings.md` | Review | T7 |

## Checkpoint

- completed：T1–T7 implementation、verification、commit isolation、deterministic build、release rehearsal，以及 workflow verify/review/archive。
- current：root adoption status 与 ADK gitlink commit。
- open：root commit；remote publish/tag/真实双 runtime certification 均不在范围。
- retry budget：无同根因重复失败超过 2 次；所有负结果均有修复或明确拒绝决策。
- stop condition：pass after root commit。
