# Safe archive restore negative results

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-10-20 | Public restore safely rejects an invalid archive | Independent source review at a17e7e61 | rejected | Target was deleted before tar read and top-level identity was unchecked |
| 2026-10-20 | Public backup CLI initializes its repository root | First actual test_archive_restore run | 1 failure among 8 tests; ROOT_DIR unbound | Fixed the entry-point initialization, retained the regression |
| 2026-10-20 | A failed compensation permits cleanup of staging | Inject commit and compensation I/O failure | Original sentinel remains in previous; candidate remains in payload | Cleanup would delete the only recoverable original directory |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| bash tests/test_archive_restore.sh (first actual run) | 1 | CLI regression found uninitialized ROOT_DIR | tests/test_archive_restore.py public CLI case | Regression | requirements.md ACC-003 |
| bash tests/test_archive_restore.sh (after repair) | 0 | 8 tests passed, including public round trip and failure compensation | tests/test_archive_restore.py | Regression | requirements.md ACC-001 to ACC-003 |
| Independent ai/root/external_methods re-review and same 8 tests | 0 | Actual Spec/Quality pass; HARNESS-RECOVERY-001 fixed for reviewed bytes | review-findings.md after final evidence assembly | Review | design.md |
