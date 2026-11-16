# Embedded practical audit, round 2

## Scope and provenance

- Frozen baseline: `63e8f61ad9a023b4349851ebb4c9a6eca042a119` (ADK 11.3.5 candidate).
- Repository: `/workspace/scratch/2d6ca6dc3d38/agent-dev-kit`.
- Read-only review. No implementation, Skill, policy, release, git index, or remote changes were made by this reviewer.
- Read `AGENTS.md`, `docs/agent-operating-rules.md`, and the previous `docs/changes/20261116-skill-execution-fidelity/{audit,source-review}.md` before selecting findings. Prior BSP/interface/rtk changes were excluded.
- Focused review covered performance/memory, RTOS/IRQ/DMA, driver implementation and bring-up, register mapping, protocol integration, hardware/core debugging, storage migration, embedded testing, and CMake build methods. This is not a claim that all repository Skills were fully re-audited in this round.
- Native execution used GCC 14.2.0, `x86_64-linux-gnu`; no MCU, board, HIL, cross compiler, model service, paid API, or external write was exercised. `cmake`, `ninja`, and `rtk` were unavailable.
- Scratch evidence directory: `/workspace/scratch/2d6ca6dc3d38/practical-v2/`.

## Candidate 1 — ADC fixture multiplication overflows before division

**Priority:** high; real behavior defect in the runnable embedded test example.

**Current source:** `examples/embedded-test-matrix/src/adc_scale.c` clamps raw input but evaluates `(raw * reference_mv) / max_count` in `int`. The public header does not restrict the ADC to 12 bits. The fixture's three original native tests pass: zero, 12-bit full scale, and negative raw input.

**Independent expected behavior:** a valid full-scale sample (`raw == max_count`) must return `reference_mv`; clamping an above-full-scale input must preserve that result. These literal mathematical endpoint invariants do not reproduce the implementation formula as the oracle.

**Observed baseline RED:** the frozen source and unchanged original tests were compiled with real host `cc -std=c11 -Wall -Wextra -Werror -O2`. Original tests exit 0; new independent boundary cases exit 1.

| Case | Input raw/reference/max | Expected | Observed |
|---|---|---:|---:|
| 12-bit full scale | 4095 / 3300 / 4095 | 3300 | 3300 |
| 24-bit full scale | 16777215 / 3300 / 16777215 | 3300 | -28 |
| maximum int full scale | INT_MAX / 3300 / INT_MAX | 3300 | 0 |
| 24-bit clamp | 16777216 / 3300 / 16777215 | 3300 | -28 |
| zero | 0 / 3300 / 16777215 | 0 | 0 |
| invalid reference | 1 / 0 / 4095 | -1 | -1 |
| invalid maximum | 1 / 3300 / 0 | -1 | -1 |

The same source compiled with `-fsanitize=signed-integer-overflow -fno-sanitize-recover=all` exits 1 and reports:

```text
adc_scale.c:10:15: runtime error: signed integer overflow: 16777215 * 3300 cannot be represented in type 'int'
```

The observed -28/0 values are this compiler/run's symptoms, not guaranteed semantics of signed overflow.

**Evidence:** `adc-overflow-red.json` records all commands, exact timestamps, exit codes, stdout/stderr, compiler version, baseline commit, and source SHA-256 values. `reproduce-adc-overflow.py` extracts immutable source bytes from the baseline into scratch; `adc-boundaries.c` contains the independent oracle.

**Repair proposal, not implemented:** widen or otherwise check the operands before multiplication, define the supported integer range, preserve clamping/error behavior, and add meaningful full-scale/clamp/invalid-input cases to the fixture's actual C tests. Do not fix by casting only the already-overflowed product or weakening the test oracle. If choosing an `int64_t` intermediate, ensure the contract covers only operand widths whose product fits it; C does not universally require `int` to be 32 bits.

**Cost/risk:** small C implementation and test change; no Skill entry/reference expansion is needed, so profile source budgets can stay unchanged. Host proof does not establish target timing or hardware behavior. `tests/test_embedded_test_matrix_example.sh` currently inspects fixture structure; its structural PASS must remain distinct from the actual native test execution used here.

**Primary reference:** GCC 14.2 instrumentation documentation specifies that `-fsanitize=signed-integer-overflow` checks signed multiplication and other arithmetic; integer promotion semantics matter. https://gcc.gnu.org/onlinedocs/gcc-14.2.0/gcc/Instrumentation-Options.html

## Candidate 2 — Preset configure does not bind subsequent build/test/artifact paths

**Priority:** medium; concrete command-contract mismatch, with runtime reproduction still unavailable.

**Current source:** `skills/adk-cmake-cross-build/SKILL.md` Workflow 3 distinguishes preset/manual configuration, but its Commands section uses `cmake --preset <preset-name>` followed by a fixed `cmake --build build/<target>`, fixed ELF paths, and `ctest --test-dir build/<target>`.

**Independent expected behavior:** build, artifact inspection, and test execution must select the same configured binary directory and intended configuration. Official CMake 3.27 preset semantics permit arbitrary `binaryDir`; build/test presets bind their `configurePreset` to that same directory. Build/test preset names need not match the configure preset name.

**Static baseline counterexample:** `inspect-cmake-preset-paths.py` extracts the frozen Commands section and resolves its actual arguments for a valid preset whose `binaryDir` is `${sourceDir}/out/demo-release`. The documented build/test commands select `${sourceDir}/build/demo`, so both same-directory predicates are false and the inspection script exits 1. `cmake-preset-static-red.json` preserves the fixture, extracted commands, exact paths, source hash, and tool availability.

**Execution limit:** this is a static path-contract RED, not a real CMake configure/build/CTest run. No tool shim or fake CMake output was used. The environment has neither CMake nor Ninja. An old-directory successful build, multi-config mismatch, or target execution has not been observed here. Before claiming executable end-to-end repair, run a real CMake fixture with distinct old/new directory identities and multi-config selections.

**Repair proposal, not implemented:** replace the ambiguous Commands block with two explicit alternatives. When verified build/test presets exist, use the actual matching preset names; otherwise resolve the configured binary directory once and use it for build, artifact, and test steps. Keep configuration consistent for multi-config generators. Inspect the actual toolchain's binary utilities, already required by the existing workflow. Preserve the existing no-tests/error and execution-backend checks.

**Cost/risk:** modest Skill rewrite that can replace redundant lines rather than add bulk; no ratchet increase. Do not invent generic preset names or assume a configure preset always has matching build/test presets. Since `large-refactor` has only 6 bytes of reported margin, check both entry and potential full-source deltas if selected.

**Primary reference:** CMake 3.27.9 preset specification, `binaryDir`, build/test `configurePreset`, and `configuration` fields. https://cmake.org/cmake/help/v3.27/manual/cmake-presets.7.html

## Deliberately retained methods

The reviewed RTOS response-time model, GCC `.su` frame versus call-chain distinction, IRQ/DMA ownership/cache/teardown, register side effects, offline symbol identity, and storage preservation/recovery flows did not yield another reproducible defect in this pass. Do not expand these merely to add more terminology. Possible generic improvements such as perf unwinder selection or heap-profiler choice remain unselected because this pass did not establish a sufficiently concrete failure case.

## Suggested next step

Select Candidate 1 for implementation after the parent allocates the write set. Candidate 2 is eligible for a compact documentation correction, but its runtime acceptance needs a CMake-capable environment. This reviewer leaves implementation and remote changes to the parent; the repository was clean when checked after native reproduction.
