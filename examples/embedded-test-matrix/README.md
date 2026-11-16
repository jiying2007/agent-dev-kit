# Embedded Test Matrix Example

This fixture demonstrates the minimum evidence shape expected by
`adk-test-strategy` for embedded full-stack projects. It is intentionally small
and deterministic: structural checks need no toolchain; the command-example
suite compiles and executes its host C tests. Real projects can replace the
commands with board-specific entries.

## Coverage

| Layer | Example Entry | Evidence |
|---|---|---|
| Host unit | `tests/test_adc_scale.c` | actual native C tests; CMake + CTest entry |
| Cross-build smoke | `cross-build/smoke-command.txt` | toolchain command is explicit |
| QEMU/SIL | `qemu-sil/boot-smoke.md` | boot smoke command and expected log |
| HIL manual | `hil/manual-record.md` | board, fixture, operator, pending evidence |
| Fault injection | `fault-injection/watchdog-reset.md` | injected fault and expected recovery |

## Suggested Commands

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure --no-tests=error
```

From the repository root, run optimized native tests and a separate UBSan case:

```bash
python tests/test_skill_command_examples.py EmbeddedAdcExampleTests -v
```

Missing sanitizer support is an explicit skip, not a sanitized pass.
The C11 example requires `int64_t` and rejects `int` wider than 32 bits at
compile time. Endpoint, clamping and invalid-input expectations are independent
of the implementation formula; 24-bit cases run only when `int` can represent
their inputs. Host results do not establish board behavior or timing.

Hardware-backed projects must add flash/readback, boot log, signal capture or
HIL controller logs before claiming production readiness.
