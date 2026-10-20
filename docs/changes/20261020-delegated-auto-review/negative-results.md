# Delegated review negative results

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-10-20 | A fresh owner/date metadata edit proves source review | Read actual Harness consumer and independent baseline review | rejected | No consumed semantic record, evaluator/source digest or real review identity |
| 2026-10-20 | Existing typed installer safety proves every public recovery entry safe | Independent actual source review | HARNESS-RECOVERY-001 confirmed | Public legacy restore removed target before archive validation; addressed in the separate recovery change |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| Read-only independent baseline source and three original diff review | not-applicable | Actual AI dual verdicts; one real recovery major retained for repair | historical review-findings.md and safe-archive-restore/negative-results.md | Review | .adk/review-authorization.md and original change packages |
| tests/run_all.sh --verbose before production receipts | 1 | Historical execution summary: 101 scripts, 99 pass; Harness receipt absent and Skill entry exceeded 7200-byte budget by 33 bytes; original log unavailable after environment replacement | evidence/pre-receipt-run-summary.md | Regression | tasks.md |
| bash tests/test_skill_sop_quality.sh after concise Skill repair | 0 | Original 7200-byte budget retained; 16 governance cases and SOP quality passed | tests/test_skill_sop_quality.sh | Regression | skills/adk-code-review-loop/SKILL.md |
| bash tests/test_review_evidence.sh after lifecycle review fixes | 0 | 43 tests passed; absent policy cannot convert AI receipt into legacy approval; actual executor and independent reviewer remain separate | tests/test_review_evidence_workflow.py | Regression | design.md |

Implementation and remote gate results are recorded in the final verification report when actually completed. This record does not stand in for test execution.

## Environment recovery

On 2026-10-20 the execution environment was replaced after source review and before remote publication. The ADK candidate files and the three archived review receipts were restored from retained exact content; the canonical validator, lifecycle and recovery implementation SHA-256 values matched the independent reviewer's prior recorded values. Duplicate active material was compared with retained archive or original Git baseline bytes before removal from the active namespace. Remaining baseline fragments were moved outside the repository without overwriting their bytes. A new complete regression will produce fresh original output before release. The unavailable older raw log is not reconstructed or presented as an available artifact.
