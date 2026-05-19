# Embedded Test Matrix Example

This fixture demonstrates the minimum evidence shape expected by
`adk-test-strategy` for embedded full-stack projects. It is intentionally small
and deterministic: CI can inspect it without a toolchain, while real projects
can replace the commands with board-specific entries.

## Coverage

| Layer | Example Entry | Evidence |
|---|---|---|
| Host unit | `tests/test_adc_scale.c` | CMake + CTest command shape |
| Cross-build smoke | `cross-build/smoke-command.txt` | toolchain command is explicit |
| QEMU/SIL | `qemu-sil/boot-smoke.md` | boot smoke command and expected log |
| HIL manual | `hil/manual-record.md` | board, fixture, operator, pending evidence |
| Fault injection | `fault-injection/watchdog-reset.md` | injected fault and expected recovery |

## Suggested Commands

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

Hardware-backed projects must add flash/readback, boot log, signal capture or
HIL controller logs before claiming production readiness.
