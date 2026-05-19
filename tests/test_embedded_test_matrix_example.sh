#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EXAMPLE_DIR="$ROOT_DIR/examples/embedded-test-matrix"

[[ -f "$EXAMPLE_DIR/CMakeLists.txt" ]] || {
  echo "[FAIL] missing CMakeLists.txt" >&2
  exit 1
}

[[ -f "$EXAMPLE_DIR/tests/test_adc_scale.c" ]] || {
  echo "[FAIL] missing host unit test" >&2
  exit 1
}

rg -q "enable_testing" "$EXAMPLE_DIR/CMakeLists.txt" || {
  echo "[FAIL] CMake example does not enable testing" >&2
  exit 1
}

rg -q "add_test" "$EXAMPLE_DIR/CMakeLists.txt" || {
  echo "[FAIL] CMake example does not register ctest" >&2
  exit 1
}

rg -q "arm-none-eabi-gcc" "$EXAMPLE_DIR/cross-build/smoke-command.txt" || {
  echo "[FAIL] cross-build smoke command missing" >&2
  exit 1
}

rg -q "qemu-system-arm" "$EXAMPLE_DIR/qemu-sil/boot-smoke.md" || {
  echo "[FAIL] qemu/sil smoke command missing" >&2
  exit 1
}

rg -q "evidence_required" "$EXAMPLE_DIR/hil/manual-record.md" || {
  echo "[FAIL] HIL manual record missing evidence requirements" >&2
  exit 1
}

rg -q "watchdog reset" "$EXAMPLE_DIR/fault-injection/watchdog-reset.md" || {
  echo "[FAIL] fault injection example missing watchdog recovery" >&2
  exit 1
}

echo "[PASS] embedded test matrix example"
