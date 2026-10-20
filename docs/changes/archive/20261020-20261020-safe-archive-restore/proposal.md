# Preserve the selected target during public archive restoration

## 问题陈述（单问题）

HARNESS-RECOVERY-001 demonstrates that the documented legacy restore deletes the target before validating an archive and can unpack to an unintended basename. Preserve the selected target until a complete, safe replacement is ready.

## 上下文充分性检查

The independent reviewer read the actual public shell restore, its documentation, the existing typed transaction core and fault-injection tests. The coordinator then exercised the public CLI and discovered its uninitialized ROOT_DIR variable as another blocker in the same entry point.

## Core/Optional 边界检查

Reuse the existing typed installation transaction module, bounded regular reads and target lock. Keep the public shell command; do not add a new subsystem or dependency.

## 变更重复性检查

Managed-install rollback uses signed inventory and installation receipts. Ordinary directory tar backups have a different format; they now share the same transaction authority and locking primitive without pretending to be install receipts.

## Breaking Change 检查

Ordinary directory archives retain their supported round trip. Unsafe links/special members, a different top-level basename, oversized archives and an unresolved earlier restore are explicitly rejected before target replacement. The original implementation provided no safe meaning for those inputs.

## Spec 链路检查

Requirements/design/tasks were recorded before implementation. Deterministic negative tests and an independent repair review must close the actual finding before the recovery dimension is renewed.

## Canonical Change Contract

| Requirement ID | Requirement | Operation | Target | Affected Surface | Acceptance ID | Acceptance Criterion | Task ID | Verification ID | Evidence Target |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | Validate before target replacement | MODIFIED | Public restore | installation_transaction.py | ACC-001 | Corrupt, wrong-target and unsafe archives preserve original sentinel bytes | TASK-002 | VERIFY-002 | tests/test_archive_restore.py |
| REQ-002 | Preserve recovery material on failure | ADDED | Archive staging and compensation | existing transaction core | ACC-002 | Extraction/commit/second compensation failures retain original content | TASK-002 | VERIFY-002 | tests/test_archive_restore.py |
| REQ-003 | Preserve valid public CLI behavior | MODIFIED | backup-rollback.sh | thin restore adapter | ACC-003 | Actual CLI backup/restore round trip succeeds and wrong basename fails safely | TASK-003 | VERIFY-003 | tests/test_archive_restore.py and independent review |

## 安装范围与依赖边界

Only existing standard-library and typed-core dependencies are used. No provider, installed runtime, secret or external service is involved. The transaction source remains under its existing 30,000-byte budget.

## Prompt 回归证据计划

No prompt content changes. Before/after evidence is the actual restore control-flow diff and executable filesystem regression; this does not establish runtime or model performance.

## 收敛模式与退出条件

The eight focused tests must pass, existing installation/full regression must remain valid, and an independent reviewer must confirm the finding is fixed. Preserve source/CI/release boundaries and use the normal versioned protected delivery path.
