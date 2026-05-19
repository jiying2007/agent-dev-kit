#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

MCU_ROOT="$TMP_DIR/mcu"
SOC_ROOT="$TMP_DIR/soc"
OUT_DIR="$TMP_DIR/out"
RUNNER_STDOUT="$TMP_DIR/runner.out"

mkdir -p "$MCU_ROOT/scripts" "$SOC_ROOT/tools/firmware-release-tools" "$SOC_ROOT/tools/ota-packager"

cat > "$MCU_ROOT/scripts/setup-nas-mount.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--check" ]]; then
  echo "NAS check OK"
  exit 0
fi
echo "unsupported setup-nas-mount args: $*" >&2
exit 2
SH

cat > "$MCU_ROOT/scripts/firmware-release.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

cmd="${1:-}"
shift || true

case "$cmd" in
  --help|-h)
    echo "firmware-release stub"
    ;;
  profile)
    echo '{"project":"mm32spin023c","layout":{"appAddress":"0x08001800"}}'
    ;;
  check-package)
    package_dir="${1:-}"
    if [[ -f "$package_dir/package_manifest.json" ]]; then
      echo "[OK] package manifest and checksums are valid"
      exit 0
    fi
    echo "[ERROR] missing manifest: $package_dir/package_manifest.json"
    exit 2
    ;;
  package-external)
    output_dir=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --output-dir)
          output_dir="$2"
          shift 2
          ;;
        *)
          shift
          ;;
      esac
    done
    [[ -n "$output_dir" ]] || exit 2
    package_dir="$output_dir/mm32spin023c_firmware_bundle"
    mkdir -p "$package_dir"
    printf '{"schemaVersion":"2.0","validation":{"passed":true}}\n' > "$package_dir/package_manifest.json"
    printf 'abc *package_manifest.json\n' > "$package_dir/checksums.sha256.txt"
    printf '{"firmwareBin":"mm32spin023c_app.bin"}\n' > "$package_dir/ota_upgrade_plan.json"
    printf 'quick guide\n' > "$package_dir/FLASHING.txt"
    cat > "$package_dir/burn_firmware.py" <<'PY'
#!/usr/bin/env python3
print("burn dry-run")
PY
    cat > "$package_dir/erase_and_burn.py" <<'PY'
#!/usr/bin/env python3
import sys
if "--force-erase" in sys.argv:
    print("factory dry-run")
    raise SystemExit(0)
print("[ERROR] Refusing chip erase because the package reserves a data partition.")
raise SystemExit(3)
PY
    cat > "$package_dir/readback_verify.py" <<'PY'
#!/usr/bin/env python3
print("readback dry-run")
PY
    ;;
  publish-nas)
    echo '{"status":"would-publish"}'
    ;;
  *)
    echo "unsupported firmware-release cmd: $cmd" >&2
    exit 2
    ;;
esac
SH

cat > "$SOC_ROOT/build.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "build stub"
  exit 0
fi

mode="${1:-}"
shift || true
allow_dirty=0
for arg in "$@"; do
  [[ "$arg" == "--allow-dirty" ]] && allow_dirty=1
done

case "$mode" in
  verify|self-check)
    if [[ "$allow_dirty" -eq 0 ]]; then
      echo "ERROR: main repo has uncommitted changes" >&2
      exit 1
    fi
    echo "[build] mode=$mode done"
    ;;
  modules-status)
    echo "name kind dirty upstream"
    ;;
  *)
    echo "unsupported build mode: $mode" >&2
    exit 2
    ;;
esac
SH

cat > "$SOC_ROOT/tools/firmware-release-tools/resolve-latest-release.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
[[ "${1:-}" == "--self-test" ]] && { echo ok; exit 0; }
exit 2
SH

cat > "$SOC_ROOT/tools/ota-packager/ota-packager.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "self-test" ]]; then
  echo '{"ok":true}'
  exit 0
fi
exit 2
SH

chmod +x \
  "$MCU_ROOT/scripts/setup-nas-mount.sh" \
  "$MCU_ROOT/scripts/firmware-release.sh" \
  "$SOC_ROOT/build.sh" \
  "$SOC_ROOT/tools/firmware-release-tools/resolve-latest-release.sh" \
  "$SOC_ROOT/tools/ota-packager/ota-packager.sh"

"$ROOT_DIR/scripts/run-embedded-production-field-pilot.sh" \
  --mcu-root "$MCU_ROOT" \
  --soc-root "$SOC_ROOT" \
  --out "$OUT_DIR" \
  >"$RUNNER_STDOUT"

[[ -f "$OUT_DIR/evidence.md" ]] || {
  echo "[FAIL] evidence.md was not generated" >&2
  exit 1
}

[[ -f "$OUT_DIR/summary.json" ]] || {
  echo "[FAIL] summary.json was not generated" >&2
  exit 1
}

rg -q '"status": "pass"' "$OUT_DIR/summary.json" || {
  echo "[FAIL] pilot runner summary did not pass" >&2
  cat "$OUT_DIR/summary.json" >&2
  exit 1
}

rg -q 'mcu-erase-protection' "$RUNNER_STDOUT" || {
  echo "[FAIL] expected erase protection step was not executed" >&2
  exit 1
}

rg -q 'pass-expected-failure' "$OUT_DIR/evidence.md" || {
  echo "[FAIL] expected negative evidence was not recorded" >&2
  exit 1
}

echo "[PASS] embedded production field pilot runner"
