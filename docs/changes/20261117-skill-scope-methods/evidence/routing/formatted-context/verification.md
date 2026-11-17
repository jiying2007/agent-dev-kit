# Formatted domain-name regression

Baseline: `3f80b613bf18cd121e3c782cc0a8d69c646f078d`. The independent review found that unconditionally removing inline quotation contents rejected valid MCU, RTOS, Zephyr and embedded host-model targets. This follow-up corrects that false negative without changing the domain vocabulary, Skill entry, manifest, permissions or export contract.

## Red to green

The new `test_embedded_unit_formatted_scope_preserves_task_context` was first run against the baseline implementation. All seven positive subcases failed; the nine negative controls passed. `red-tests.txt` preserves that actual failure. After the fix, `green-tests.txt` records the same method passing, and `matrix-final.txt` records the original 20 methods plus this new method passing (**21/21**).

The independent review's 14-case baseline is preserved in `before.json`, copied verbatim in data from `/workspace/scratch/fe8de3b42084/independent-scope-review/raw/routing-neighbors.stdout.txt`. `after.json` replays those exact prompts through the public matcher: **10/14 → 14/14** expected outcomes. All 14 after-results keep `mutation_permission=deny`. The baseline copy is independent-review evidence; the red test and after replay were executed by the implementer.

## Small format correction

Fenced code remains excluded. Ordinary paired inline backticks and quotation marks now lose only their delimiters, retaining the enclosed technical name. The existing local negation matcher therefore still rejects forms such as `不是` followed by a backtick-wrapped `MCU`, and `not` followed by quoted `embedded`.

A bounded syntax rule still discards quoted content introduced at the start of a clause by `文档写着`, `文档示例`, `示例`, `引述`, `example`, `quote` or `quoted`. This preserves explicit quoted-example negatives without making punctuation alone a reason to reject a real task target. The marker vocabulary describes presentation syntax; domain vocabulary stays in the existing Skill metadata. No target-name list or general background classifier was introduced.

The matcher remains lexical. It does not resolve every unmarked quotation or unrelated background construction, and the runtime Fit/Target gate remains required. Native host behavior and model token effect remain **not-measured**.

## Scope and checks

Changed source files: `_matcher_kernel.py`, `test_skill_trigger_matrix.py`, and the `match` documentation in `docs/commands.md`. The Skill entry remains 3066 bytes and version 1.1.8. No manifest, Profile ratchet, project-version field or permission change was made by this implementer.

Commands ran through `/workspace/scratch/fe5385ca063a/verification-tools/rtk bypass`, with `PYTHONPATH=src:tests` and `PYTHONDONTWRITEBYTECODE=1` for tests:

- New regression method: expected exit 1 before, exit 0 after.
- Full `python3 -m unittest test_skill_trigger_matrix`: exit 0, 21 tests.
- Independent 14-prompt replay: exit 0, 14 expected outcomes.
- `git diff --check`: exit 0.

The coordinator stopped the earlier full regression before these source edits and owns a fresh full regression. This evidence does not claim that the interrupted run qualifies the revised source. No commit or push was performed by this implementer.
