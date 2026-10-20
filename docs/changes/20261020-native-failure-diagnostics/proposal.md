# Retain safe diagnostics for failed hosted Native campaigns

## 问题陈述（单问题）

The hosted Claude Native workflow redirects prepare/run/finalize summaries into runner-temporary files. A non-zero campaign exit skips all later default-success packaging and upload steps. The failed job remains correctly failed, but the structured failure context is lost when the runner is disposed.

## 上下文充分性检查

Read the exact hosted workflow, Native campaign CLI, v2 plan/evidence schemas, strict JSON reader, Native runbook and module budget. The observed source path is sufficient to demonstrate the missing failure-artifact path. No real provider campaign was executed during this review. Local provider CLIs and credentials were unavailable; retained public manual-run history contained no Native campaign run.

## Core/Optional 边界检查

Add a small typed-core metadata collector called only by the existing optional hosted Native workflow. Reuse the existing v2 schema validator and bounded JSON reader. Do not add a qualification system, Skill, runtime dependency or paid execution path.

## 变更重复性检查

The existing success artifact index is a candidate-evidence package and requires finalized receipt files. It cannot safely be reused after an early failure. A failure-only fixed metadata file provides the missing behavior without relaxing candidate packaging or registry checks.

## Breaking Change 检查

This is an additive internal diagnostic artifact. Existing public CLI, receipt, target-contract and registry schemas are unchanged. New diagnostic fields have no certification or release authority.

## Spec 链路检查

`requirements.md` defines the three acceptance criteria; the canonical table below is the single task and verification authority for this change. Historical Native and Owner tracker status and review dates remain separate evidence.

## Canonical Change Contract

| Requirement ID | Requirement | Operation | Target | Affected Surface | Acceptance ID | Acceptance Criterion | Task ID | Verification ID | Evidence Target |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | Preserve failed-phase diagnostics | ADDED | Hosted Native failure branch | native_campaign_diagnostics.py and native workflow | ACC-001 | Failed and skipped phases are distinguishable; original failure remains | TASK-001 | VERIFY-001 | tests/test_native_campaign_diagnostics.py |
| REQ-002 | Bound and sanitize retained data | ADDED | Diagnostic metadata writer | strict reader and fixed projection | ACC-002 | Unsafe files and JSON are rejected; free text and raw data never copied | TASK-002 | VERIFY-002 | tests/test_native_campaign_diagnostics.py |
| REQ-003 | Preserve Native authority boundaries | MODIFIED | Existing hosted workflow and runbook | diagnostic-only artifact path | ACC-003 | Signing and promotion remain success-only; diagnostics have no authority | TASK-003 | VERIFY-003 | workflow contract tests and native-campaign.md |

## 安装范围与依赖边界

The helper ships with the existing Python package and uses only standard-library code plus the already-declared schema dependency. No new installed asset, Skill, agent process, CI job, provider or model is added. The module must remain below the existing default 30,000-byte source budget.

## Prompt 回归证据计划

No prompt or semantic canary changes. Before: a failed run skips the sole artifact upload. After: a separate failure-only upload can contain one sanitized metadata JSON. Tests verify this control-flow difference and unchanged successful signing and candidate upload conditions; they do not claim improved model outcomes.

## 收敛模式与退出条件

Finish when deterministic failure, privacy, filesystem and workflow-boundary tests pass, strict typing and formatting pass, the change governance check passes and the existing Native regression remains valid. Hosted execution evidence remains unavailable until a separately authorized real campaign runs with actual resources. Source tests cannot close Native certification, Owner review or field-evidence trackers.

External method intake is limited to GitHub's documented default `success()` behavior and failure-log collection guidance: https://docs.github.com/en/actions/reference/workflows-and-actions/expressions . Security rationale: https://docs.github.com/en/actions/reference/security/secure-use .
