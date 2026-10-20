# Safe public backup restoration

Independent reviewer `ai/root/external_methods` confirmed HARNESS-RECOVERY-001 in source `a17e7e61a01845cc1b1165c9f9137b689bb2e1de` at 2026-10-20T06:58:25Z. The still-documented shell restore removes the destination before opening the archive and restores its original basename rather than verifying the selected target.

- REQ-001 / ACC-001: Reject corrupt archives, wrong top-level identity, traversal, links, special entries and excessive archive sizes before moving the existing target; preserve original sentinel bytes.
- REQ-002 / ACC-002: Extract bounded regular content into private same-filesystem staging and atomically replace the selected target under the existing target lock. Compensate a failed commit; preserve recovery material if extraction, commit or compensation fails.
- REQ-003 / ACC-003: Preserve the public backup/restore CLI and ordinary existing directory archives. Keep the shell as a thin caller of the existing typed transaction core, with deterministic actual-operation failure tests.

This separate recovery change is necessary to resolve the real finding before a full Harness review can pass. It is not evidence of past user data loss or a new installation subsystem.
