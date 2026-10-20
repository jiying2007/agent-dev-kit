# Safe archive restore tasks

## Ownership 与并行冲突检查

The coordinating implementer `ai/root` owns `scripts/backup-rollback.sh`, the new archive restore functions in `installation_transaction.py`, focused archive tests and this evidence package. Other agents do not write these files. Independent reviewer `ai/root/external_methods` owns no source mutations.

- [x] TASK-001: Freeze the observed finding and target-preservation acceptance. VERIFY-001: original source control flow and independent review.
- [x] TASK-002: Implement bounded staged restoration in the existing typed transaction core. VERIFY-002: unsafe archive and ordinary restoration tests.
- [x] TASK-003: Validate actual compensation failures and the public CLI; obtain independent re-review. VERIFY-003: test logs and independent Spec/Quality conclusions.

## 轻量工件与收敛结论

Requirements and design are frozen before implementation. Acceptance requires fresh deterministic negative tests and actual independent re-review; Harness recovery remains unapproved until those complete.
