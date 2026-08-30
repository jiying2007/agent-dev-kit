# Verification Evidence：effect-comparator-v1

| Command | Result | Scope |
|---|---|---|
| `rtk bash tests/test_effect_comparator.sh` | 3/3 pass | metrics/delta、coverage、population、duplicate、environment、secret |
| `rtk bash tests/test_run_evidence.sh` | 4/4 pass | child evidence binding |
| `rtk bash tests/test_format.sh` | pass | source/JSON/doc format |

当前仅是 development/test evidence；Python 3.11/3.12 与 aggregate 由 umbrella 最终冻结树复验。
