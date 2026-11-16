# T3/T4 implementation handoff

Source writes are finished. The allocated nine-file diff and final hashes are in `allocated-source.patch` and `handoff.json`. No commits, version/catalog/fixture integration, remote writes, or changes outside the parent's assigned source set were performed.

## Implemented

- ADC casts before multiplication, enforces `INT_MAX <= INT32_MAX` at compile time, documents the `int64_t`/C11 requirement, and preserves clamping/error behavior. Fourteen host test vectors on this machine include original positives, INT_MAX endpoints, invalid inputs and capability-guarded 24-bit cases. Expected values use endpoint/clamping invariants rather than the implementation formula.
- The existing command-example unittest entry now compiles/runs the actual ADC C test source. UBSan has a separate instrumentation/runtime probe; unavailable support is a visible independent skip, while failures in the actual example remain failures.
- ADC's CMake target declares PRIVATE `c_std_11`; its existing cross smoke explicitly requests `-std=c11`. The public header/test syntax does not impose C11 on consumers.
- CMake 1.0.5 has mutually exclusive preset/manual blocks, consistent selected configuration, actual directory/artifact inputs, different allowed configure/build/test preset names, explicit execution backend handling and `--no-tests=error`.
- Five real CMake cases execute the current published bash blocks: preset directory/configuration/ELF/CTest identity with an untouched old build, manual identity, empty tests, compile-only, and the actual ADC CMake project under a strict C90 default with C11 required by its implementation target. No duplicate equivalent build implementation or fake tool is used.
- Performance 1.1.6 maps heap peak/timeline to Massif, errors/leaks to Memcheck, and resident memory to a separate RSS measurement. It states sampling/time-unit and instrumentation overhead limits and explicit unavailable tools.

## Actual observations

| Evidence | Actual result |
|---|---|
| `adc-native-red.json` | New shipped C tests + original implementation: native and UBSan both failed; original three cases still passed |
| `adc-native-green.json` | Same tests + widened implementation: native and UBSan both passed |
| `command-examples-final-local.json` | 26 methods: 21 passed, 5 explicitly skipped because cmake/ctest/ninja are unavailable |
| `cmake-shell-syntax.json` | Actual three published bash blocks passed `bash -n`; no CMake execution |
| `cmake-ci-tool-refusal.json` | Local capability negative test with `GITHUB_ACTIONS=true` failed before fixture execution, as intended; not a GitHub run |
| `portfolio-local.json` | Seven existing portfolio checks passed |
| `adc-structural-check.json` | Existing structural example check passed; not substituted for native execution |
| `handoff.json` | Final source hashes, byte deltas, allocated patch hash and whitespace check |

CMake source bytes are 4127 -> 4125; performance source bytes are 3094 -> 3094. No profile budget was raised; the parent must perform final eight-profile integration validation. CMake and Valgrind runtime behavior were not observed locally. Cross-build/MCU/HIL behavior is not claimed.

## Primary sources used

- CMake 3.27.9 preset directory/name/configuration semantics: https://cmake.org/cmake/help/v3.27/manual/cmake-presets.7.html
- GCC 14.2 signed overflow instrumentation: https://gcc.gnu.org/onlinedocs/gcc-14.2.0/gcc/Instrumentation-Options.html
- Massif heap profiling/snapshots/time units: https://valgrind.org/docs/manual/ms-manual.html
- Memcheck error/leak detection: https://valgrind.org/docs/manual/mc-manual.html
- Linux process resident-memory accounting: https://docs.kernel.org/filesystems/proc.html

The parent's independent review and actual CI run remain necessary before release. In GitHub Actions, any missing required CMake fixture tool is a failure, so a green integration run cannot be obtained by silently skipping these five methods.
