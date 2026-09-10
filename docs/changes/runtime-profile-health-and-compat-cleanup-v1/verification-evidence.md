# 验证证据

- `tests/test_live_profile_drift.py`：3 tests pass，覆盖 team-collab managed asset、rogue skill fail-closed 和 inactive plugin filtering。
- `tests/test_apply_prune.py`：9 tests pass，覆盖 retired live path 的 backup-bound delete。
- `scripts/build.sh --profile team-collab`、`doctor.sh --scope all`、plan dry-run 和 post-apply `check.sh`：通过。
- `llm_agent` runtime health、live footprint、routing 和 targets：均为 pass。
