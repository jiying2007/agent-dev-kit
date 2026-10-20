# Safe archive restore design

Keep `scripts/backup-rollback.sh` as the public entry point. Delegate restore to `installation_transaction.restore_archive`, alongside existing transactional installation recovery, and reuse `TargetLock` and the bounded regular-file reader. Reject target or archive symlink aliases and filesystem-root targets.

Verify the full gzip stream under an expanded-size budget, inspect a bounded tar member inventory and require one canonical top-level directory matching the selected target. Permit only unique ordinary files/directories, with no links, devices, sparse files or path traversal. Extract regular bytes manually into a private sibling staging directory; never call tar's filesystem extraction methods.

Only after complete extraction, move the existing target to `previous` and the staged payload to the selected target with same-filesystem atomic renames. If replacement fails, restore `previous`. Retain the staging directory and a diagnostic failure message when any extraction/commit/compensation step fails; a subsequent restore refuses retained incomplete staging. Successful restore removes staging. No existing installation receipt semantics change.

Tests exercise the public CLI round trip and direct typed implementation under real temporary filesystem operations. Mock only the failing I/O operation to prove extraction, commit and second-failure compensation boundaries. Rollback is a protected versioned revert; the fix never rewrites an existing backup archive.
