# Historical pre-receipt execution summary

This is a retained execution summary, not the original command log.

- Actual executor: `ai/root/qualification_audit`.
- Command: `tests/run_all.sh --verbose` against the ADK delegated-review candidate before production review receipts.
- Completed at: `2026-10-20T07:21:32.755762Z`.
- Reported exit: `1`.
- Reported scripts: `101`; passed: `99`; failed: `2`.
- Actual failures: production Harness review receipt absent; Skill entry was 7,233 bytes against its unchanged 7,200-byte budget.
- Original log byte count: `61000`.
- Original SHA-256 recorded at execution: `38e63bb221bb75f65549696d7f7aa2bb025aeb87c6c8532c28078e95581eff25`.

The original log was lost when the execution environment was replaced. The executor confirmed at recovery that its file and in-memory store contain no original log bytes. This summary preserves the reported historical result without claiming that the original log remains independently retrievable. The Skill size failure was subsequently repaired and its original test passed; final production Harness and complete regression results must come from new actual executions and original CI artifacts.
