# T1 routing verification

Baseline: `0973b9dce75e7bde289a9915fc58dfd53cb79b0d` (11.3.12). This is implementation evidence from `route_implementation`, not an independent review or a full CI result. The coordinator owns integration validation and final project versioning.

This snapshot predates the independent review's formatted-domain finding. The subsequent correction, current quotation semantics and 21-test result are recorded in `formatted-context/verification.md`; the original before/after artifacts below remain preserved as historical evidence.

## Result

The 12 preserved source counterexamples and positive controls move from 5/12 to 12/12 expected outcomes. Python/pytest with explicit non-embedded scope, generic Rust/cargo, generic unit tests, locally negated scope and quoted context no longer implicitly select `adk-unit-test-embedded`. MCU drivers, embedded Python host models, embedded Rust firmware and host-only execution remain eligible. A split-context request, `MCU 工程；补 UART 单测`, now selects the embedded unit Skill. Every after-probe result retains `mutation_permission=deny`.

`before.json` preserves original results and the baseline Skill hash. `after.json` replays the same prompts through the public matcher. `result.json` records source hashes and byte counts. These are selected deterministic cases; they do not estimate general routing accuracy.

## Implementation and compatibility

- The optional, non-empty `implicit_context` phrase list lives in the existing Skill source. The canonical matcher requires an affirmative domain match for implicit routing, trigger fallback, promoted primaries and secondary primary candidates. No manifest entry, IR schema, Skill inventory, permission ceiling or additional routing layer changed.
- The existing local polarity matcher is reused. Quoted strings and fenced/inline code do not establish context. Domain and task may appear in different sentences. Explicit out-of-domain wording remains in `non_triggers`.
- Field absence preserves previous behavior. Empty, scalar, non-string or empty-phrase values fail source validation and implicit consumption. Explicit single-Skill diagnostics retain trigger/non-trigger behavior, including supporting Skills; they do not acquire write permission.
- Claude Code and OpenCode exports retain their existing frontmatter contract. The new field is not exported as a native host gate. Description and body express the MCU/RTOS plus host-model scope. Native host discovery and actual model token savings are **not-measured**.

The check is lexical: an unquoted, affirmative MCU mention in unrelated background can still satisfy the context condition. The implementation deliberately preserves normal split-sentence descriptions rather than introducing a general background classifier. Explicit task-domain exclusions and runtime Fit/Target gates remain necessary. No claim is made to solve every quoted, multilingual or ambiguous-background construction.

## Tests actually run

All shell entrypoints ran through `/workspace/scratch/fe5385ca063a/verification-tools/rtk bypass`. The commands below identify the underlying checks; Python unit tests used `PYTHONPATH=src:tests`.

| Check | Result | Raw evidence |
| --- | --- | --- |
| Two initial scope and explicit-diagnostic test methods on baseline | Expected red: 10 failing subcases | `red-tests.txt` |
| `python3 -m unittest test_skill_trigger_matrix` | 20 tests passed | `trigger-matrix-final.txt` |
| `python3 -m unittest test_skill_governance test_routing_ir_contract test_external_domain_methods` | 30 tests passed | `routing-contracts.txt` |
| `bash tests/test_match_effectiveness.sh` | 41 shell checks and 4 Python tests passed | `match-effectiveness.txt` |
| `bash tests/test_boundary_conditions_match.sh` | 39 checks passed | `boundary-final.txt` |
| `_validate_skills(Manifest.load(...), strict=True, failures)` | No failures | `skill-validation.json` |
| `git diff --check` | Passed | Observed command exit 0 |
| `python3 -m ruff check` on the changed Python files | Not run: interpreter has no `ruff` module | Coordinator to use the quality environment |

The new matrix coverage includes absent/invalid metadata, both implicit consumption paths, same-group promotion, secondary candidates, explicit supporting diagnostics, non-triggers, unchanged permissions and both native export formats. Fixtures use the actual matcher and exporter without mocking their behavior.

Two legacy routing fixtures now say `MCU 工程写单元测试`; the Unicode mixed fixture says `Write 单元测试 for MCU module`. Their original purpose remains a positive embedded route / Unicode check. Generic `写单元测试` is now separately required to abstain. During iteration, the existing discovery tests caught omitted `单元测试` and exclusion phrasing in a compressed description; both source requirements were restored before the final 20-test pass.

## Files and size

Implementation files are `_matcher_kernel.py`, `matcher.py`, `validation_contract.py`, the embedded unit Skill, the two existing match shell suites, `test_skill_trigger_matrix.py` and the `match` section of `docs/commands.md`.

The Skill is version 1.1.8, dated 2026-11-17. Its entry changes from 3068 to 3066 UTF-8 bytes (**−2 B**), with no new reference file. Compression preserves the target/test-seam checks, host/compile-only/SIL/HIL distinctions, authorization boundary, defect regression, hardware gaps and MC/DC caveat. The original eight Profile ratchets were not edited. No commit or push was performed by this implementer.
