#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

MCU_ROOT="${MCU_RELEASE_TOOLS_ROOT:-}"
SOC_ROOT="${SOC_BUILD_ROOT:-}"
PROFILE="mm32spin023c"
VERSION="0.0.9"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${ADK_PILOT_OUT:-/tmp/adk-pilot/embedded-production-field-readiness/${TIMESTAMP}}"
SKIP_MCU=0
SKIP_SOC=0
SIMULATE_DEVICE=0

usage() {
  cat <<USAGE
Usage:
  scripts/run-embedded-production-field-pilot.sh --mcu-root <path> --soc-root <path> [options]

Collects dry-run evidence for adk-production-field-readiness without flashing,
publishing, tagging, mounting, or modifying source worktrees.

Options:
  --mcu-root <path>   Firmware release tools root.
  --soc-root <path>   SoC/Linux build root containing build.sh.
  --out <path>        Evidence output directory. Default: ${OUT_DIR}
  --profile <name>    MCU release profile. Default: ${PROFILE}
  --version <x.y.z>   Sample firmware version. Default: ${VERSION}
  --skip-mcu          Skip MCU release evidence.
  --skip-soc          Skip SoC build evidence.
  --simulate-device   Generate deterministic simulated flash/readback/boot/HIL/OTA/rollback evidence.
  -h, --help          Show this help.

Environment aliases:
  MCU_RELEASE_TOOLS_ROOT, SOC_BUILD_ROOT, ADK_PILOT_OUT
USAGE
}

require_value() {
  local opt="$1"
  local val="${2:-}"
  [[ -n "$val" && "$val" != --* ]] || {
    echo "[FAIL] $opt requires a value" >&2
    exit 1
  }
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mcu-root)
      require_value "$1" "${2:-}"
      MCU_ROOT="$2"
      shift 2
      ;;
    --soc-root)
      require_value "$1" "${2:-}"
      SOC_ROOT="$2"
      shift 2
      ;;
    --out)
      require_value "$1" "${2:-}"
      OUT_DIR="$2"
      shift 2
      ;;
    --profile)
      require_value "$1" "${2:-}"
      PROFILE="$2"
      shift 2
      ;;
    --version)
      require_value "$1" "${2:-}"
      VERSION="$2"
      shift 2
      ;;
    --skip-mcu)
      SKIP_MCU=1
      shift
      ;;
    --skip-soc)
      SKIP_SOC=1
      shift
      ;;
    --simulate-device)
      SIMULATE_DEVICE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "$SKIP_MCU" -eq 0 ]]; then
  [[ -n "$MCU_ROOT" ]] || { echo "[FAIL] --mcu-root is required unless --skip-mcu is used" >&2; exit 1; }
  [[ -d "$MCU_ROOT" ]] || { echo "[FAIL] MCU root not found: $MCU_ROOT" >&2; exit 1; }
  [[ -x "$MCU_ROOT/scripts/firmware-release.sh" || -f "$MCU_ROOT/scripts/firmware-release.sh" ]] || {
    echo "[FAIL] firmware-release.sh not found under MCU root" >&2
    exit 1
  }
fi

if [[ "$SKIP_SOC" -eq 0 ]]; then
  [[ -n "$SOC_ROOT" ]] || { echo "[FAIL] --soc-root is required unless --skip-soc is used" >&2; exit 1; }
  [[ -d "$SOC_ROOT" ]] || { echo "[FAIL] SoC root not found: $SOC_ROOT" >&2; exit 1; }
  [[ -f "$SOC_ROOT/build.sh" ]] || { echo "[FAIL] build.sh not found under SoC root" >&2; exit 1; }
fi

LOG_DIR="$OUT_DIR/logs"
EVIDENCE_MD="$OUT_DIR/evidence.md"
SUMMARY_JSON="$OUT_DIR/summary.json"
rm -rf "$LOG_DIR" "$OUT_DIR/mcu-samples" "$OUT_DIR/mcu-package" "$OUT_DIR/nas-release"
rm -rf "$OUT_DIR/sim-device"
mkdir -p "$LOG_DIR"

escape_cell() {
  printf '%s' "$1" | sed 's/|/\\|/g'
}

quote_cmd() {
  local out=""
  local item
  for item in "$@"; do
    printf -v item '%q' "$item"
    out+="${item} "
  done
  printf '%s' "${out% }"
}

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9][^a-z0-9]*/-/g; s/^-//; s/-$//'
}

{
  echo "# Embedded Production Field Readiness Evidence"
  echo
  echo "- generated_at: $(date -Iseconds)"
  echo "- profile: ${PROFILE}"
  echo "- version: ${VERSION}"
  echo "- output_dir: ${OUT_DIR}"
  echo
  echo "## Evidence Index（命令级）"
  echo "| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |"
  echo "|---|---:|---|---|---|---|"
} > "$EVIDENCE_MD"

STEP=0
FAILURES=0
WARNINGS=0

run_step() {
  local mode="$1"
  local name="$2"
  local summary="$3"
  local cwd="$4"
  shift 4

  STEP=$((STEP + 1))
  local slug
  slug="$(slugify "$name")"
  local log_file="$LOG_DIR/$(printf '%02d' "$STEP")-${slug}.log"
  local cmd_display
  cmd_display="$(quote_cmd "$@")"

  local rc=0
  set +e
  (cd "$cwd" && "$@") >"$log_file" 2>&1
  rc=$?
  set -e

  local result="pass"
  case "$mode" in
    required)
      if [[ "$rc" -ne 0 ]]; then
        result="fail"
        FAILURES=$((FAILURES + 1))
      fi
      ;;
    allow)
      result="observed"
      if [[ "$rc" -ne 0 ]]; then
        WARNINGS=$((WARNINGS + 1))
      fi
      ;;
    expect-fail)
      if [[ "$rc" -eq 0 ]]; then
        result="fail-expected-nonzero"
        FAILURES=$((FAILURES + 1))
      else
        result="pass-expected-failure"
      fi
      ;;
    *)
      echo "[FAIL] internal error: unsupported step mode $mode" >&2
      exit 1
      ;;
  esac

  printf '| `%s` | %s | %s (%s) | `%s` | Skill | adk-production-field-readiness |\n' \
    "$(escape_cell "$cmd_display")" \
    "$rc" \
    "$(escape_cell "$summary")" \
    "$result" \
    "$log_file" >> "$EVIDENCE_MD"

  echo "[STEP] $name rc=$rc result=$result log=$log_file"
}

write_sample_ihex() {
  local sample_dir="$1"
  local app_hex="$2"
  mkdir -p "$sample_dir"
  cat > "$sample_dir/boot.hex" <<'EOF'
:020000040800F2
:080000000010002009000008B7
:00000001FF
EOF
  cat > "$app_hex" <<'EOF'
:020000040800F2
:08180000001000200918000887
:00000001FF
EOF
  echo "[INFO] sample_ihex_dir=$sample_dir"
}

write_simulated_device_ctl() {
  local sim_dir="$1"
  local simctl="$sim_dir/simctl.sh"
  mkdir -p "$sim_dir"
  cat > "$simctl" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

cmd="${1:-}"
state="${2:-}"
profile="${3:-sim-board}"
version="${4:-0.0.0}"

[[ -n "$cmd" && -n "$state" ]] || {
  echo "usage: simctl.sh <flash|readback|boot|hil|ota|rollback|field-package> <state-dir> [profile] [version]" >&2
  exit 2
}

mkdir -p "$state"

hash_state() {
  printf '%s' "$1" | sha256sum | awk '{print $1}'
}

case "$cmd" in
  flash)
    digest="$(hash_state "${profile}:${version}:flash")"
    printf 'profile=%s\nversion=%s\ndigest=%s\n' "$profile" "$version" "$digest" > "$state/flash-report.txt"
    printf '%s\n' "$digest" > "$state/readback.expected"
    printf '%s\n' "$version" > "$state/current-version"
    printf 'slot=A\n' > "$state/slot-state"
    echo "SIM_FLASH_OK profile=$profile version=$version digest=$digest"
    ;;
  readback)
    [[ -f "$state/readback.expected" ]] || { echo "missing simulated flash state" >&2; exit 3; }
    expected="$(cat "$state/readback.expected")"
    actual="$(hash_state "${profile}:${version}:flash")"
    [[ "$actual" == "$expected" ]] || { echo "readback mismatch expected=$expected actual=$actual" >&2; exit 4; }
    printf 'expected=%s\nactual=%s\nresult=match\n' "$expected" "$actual" > "$state/readback-report.txt"
    echo "SIM_READBACK_OK digest=$actual"
    ;;
  boot)
    [[ -f "$state/current-version" ]] || { echo "device is not flashed" >&2; exit 3; }
    cat > "$state/boot.log" <<EOF
BOOT_OK
profile=$profile
version=$(cat "$state/current-version")
diagnostic=pass
EOF
    echo "SIM_BOOT_OK"
    ;;
  hil)
    cat > "$state/hil-report.json" <<EOF
{"profile":"$profile","version":"$(cat "$state/current-version" 2>/dev/null || printf '%s' "$version")","power_cycle":"pass","diagnostic_cli":"pass","fault_injection":"pass"}
EOF
    echo "SIM_HIL_OK"
    ;;
  ota)
    [[ -f "$state/current-version" ]] || { echo "device is not flashed" >&2; exit 3; }
    old="$(cat "$state/current-version")"
    printf '%s\n' "$old" > "$state/rollback-version"
    printf '%s\n' "$version" > "$state/current-version"
    printf 'slot=B\n' > "$state/slot-state"
    cat > "$state/ota-report.json" <<EOF
{"from":"$old","to":"$version","download":"pass","apply":"pass","boot_after_update":"pass","active_slot":"B"}
EOF
    echo "SIM_OTA_OK from=$old to=$version"
    ;;
  rollback)
    [[ -f "$state/rollback-version" ]] || { echo "missing rollback version" >&2; exit 3; }
    rollback="$(cat "$state/rollback-version")"
    current="$(cat "$state/current-version")"
    printf '%s\n' "$rollback" > "$state/current-version"
    printf 'slot=A\n' > "$state/slot-state"
    cat > "$state/rollback-report.json" <<EOF
{"from":"$current","to":"$rollback","rollback":"pass","boot_after_rollback":"pass","active_slot":"A"}
EOF
    echo "SIM_ROLLBACK_OK from=$current to=$rollback"
    ;;
  field-package)
    pkg="$state/field-package"
    mkdir -p "$pkg"
    cat > "$pkg/manifest.json" <<EOF
{"profile":"$profile","version":"$(cat "$state/current-version" 2>/dev/null || printf '%s' "$version")","contains":["flash-report","readback-report","boot-log","hil-report","ota-report","rollback-report"],"credential_material":"none"}
EOF
    printf '现场维护包（模拟）：包含启动、诊断、OTA 和回滚证据索引。\n' > "$pkg/FIELD_SERVICE_GUIDE.md"
    echo "SIM_FIELD_PACKAGE_OK path=$pkg"
    ;;
  *)
    echo "unsupported simulated device command: $cmd" >&2
    exit 2
    ;;
esac
SH
  chmod +x "$simctl"
  printf '%s\n' "$simctl"
}

if [[ "$SKIP_MCU" -eq 0 ]]; then
  SAMPLE_DIR="$OUT_DIR/mcu-samples"
  APP_HEX="$SAMPLE_DIR/app_v${VERSION}.hex"
  MCU_OUT="$OUT_DIR/mcu-package"
  PACKAGE_DIR="$MCU_OUT/${PROFILE}_firmware_bundle"
  write_sample_ihex "$SAMPLE_DIR" "$APP_HEX"

  run_step required "mcu-cli-help" "MCU release CLI is discoverable" "$MCU_ROOT" \
    bash scripts/firmware-release.sh --help
  run_step required "mcu-profile" "MCU release profile resolves layout and OTA metadata" "$MCU_ROOT" \
    bash scripts/firmware-release.sh profile "$PROFILE"
  run_step allow "mcu-nas-check" "NAS check is observed without mounting or publishing" "$MCU_ROOT" \
    bash scripts/setup-nas-mount.sh --check
  run_step expect-fail "mcu-check-before-package" "Package validation fails before manifest exists" "$MCU_ROOT" \
    bash scripts/firmware-release.sh check-package "$PACKAGE_DIR"
  run_step required "mcu-package-external" "Local MCU package, manifest, checksum and zip are generated" "$MCU_ROOT" \
    bash scripts/firmware-release.sh package-external --profile "$PROFILE" --repo "$SAMPLE_DIR" --boot "$SAMPLE_DIR/boot.hex" --app "$APP_HEX" --version "$VERSION" --output-dir "$MCU_OUT"
  run_step required "mcu-check-package" "Generated package manifest and checksums validate" "$MCU_ROOT" \
    bash scripts/firmware-release.sh check-package "$PACKAGE_DIR"
  run_step required "mcu-burn-dry-run" "Default merged image burn script is generated without flashing" "$PACKAGE_DIR" \
    python3 "$PACKAGE_DIR/burn_firmware.py" --dry-run
  run_step expect-fail "mcu-erase-protection" "Erase script refuses reserved data erase without explicit force" "$PACKAGE_DIR" \
    python3 "$PACKAGE_DIR/erase_and_burn.py" --dry-run
  run_step required "mcu-factory-recovery-dry-run" "Factory recovery script is generated only with explicit force and production-full role" "$PACKAGE_DIR" \
    python3 "$PACKAGE_DIR/erase_and_burn.py" --force-erase --role production-full --dry-run
  run_step required "mcu-readback-dry-run" "Readback verification script is generated without touching hardware" "$PACKAGE_DIR" \
    python3 "$PACKAGE_DIR/readback_verify.py" --dry-run
  run_step required "mcu-publish-nas-dry-run" "NAS publish plan reports would-publish under local release root" "$MCU_ROOT" \
    bash scripts/firmware-release.sh publish-nas --release-root "$OUT_DIR/nas-release" --batch-id adk-pilot --timestamp "$TIMESTAMP" --item "$PROFILE=$PACKAGE_DIR" --dry-run --json
fi

if [[ "$SKIP_SOC" -eq 0 ]]; then
  run_step required "soc-build-help" "SoC build modes are discoverable" "$SOC_ROOT" \
    bash build.sh --help
  run_step allow "soc-verify-clean-gate" "Default source verification gate is observed before dirty override" "$SOC_ROOT" \
    bash build.sh verify
  run_step allow "soc-self-check-clean-gate" "Default self-check gate is observed before dirty override" "$SOC_ROOT" \
    bash build.sh self-check
  run_step required "soc-verify-allow-dirty" "Read-only source verification passes with explicit dirty override" "$SOC_ROOT" \
    bash build.sh verify --allow-dirty
  run_step required "soc-self-check-allow-dirty" "SoC project/app/toolchain/OTA helper self-check passes with explicit dirty override" "$SOC_ROOT" \
    bash build.sh self-check --allow-dirty
  run_step allow "soc-modules-status" "Module status is collected for dirty/missing-link risk tracking" "$SOC_ROOT" \
    bash build.sh modules-status
  run_step required "soc-mcu-resolver-self-test" "MCU release resolver self-test passes without NAS access" "$SOC_ROOT" \
    bash tools/firmware-release-tools/resolve-latest-release.sh --self-test
  run_step required "soc-ota-packager-self-test" "OTA packager CLI self-test passes" "$SOC_ROOT" \
    bash tools/ota-packager/ota-packager.sh self-test --json
fi

if [[ "$SIMULATE_DEVICE" -eq 1 ]]; then
  SIM_DIR="$OUT_DIR/sim-device"
  SIM_STATE="$SIM_DIR/state"
  SIM_CTL="$(write_simulated_device_ctl "$SIM_DIR")"
  SIM_OTA_VERSION="${VERSION}-ota"

  run_step required "sim-device-flash" "Simulated device flash writes versioned state without hardware access" "$OUT_DIR" \
    "$SIM_CTL" flash "$SIM_STATE" "$PROFILE" "$VERSION"
  run_step required "sim-device-readback" "Simulated readback hash matches flashed state" "$OUT_DIR" \
    "$SIM_CTL" readback "$SIM_STATE" "$PROFILE" "$VERSION"
  run_step required "sim-device-boot" "Simulated boot log reports BOOT_OK and diagnostic pass" "$OUT_DIR" \
    "$SIM_CTL" boot "$SIM_STATE" "$PROFILE" "$VERSION"
  run_step required "sim-device-hil" "Simulated HIL covers power-cycle, diagnostic CLI and fault injection" "$OUT_DIR" \
    "$SIM_CTL" hil "$SIM_STATE" "$PROFILE" "$VERSION"
  run_step required "sim-device-ota" "Simulated OTA updates inactive slot and boots updated version" "$OUT_DIR" \
    "$SIM_CTL" ota "$SIM_STATE" "$PROFILE" "$SIM_OTA_VERSION"
  run_step required "sim-device-rollback" "Simulated rollback restores previous version and active slot" "$OUT_DIR" \
    "$SIM_CTL" rollback "$SIM_STATE" "$PROFILE" "$VERSION"
  run_step required "sim-device-field-package" "Simulated field service package is generated without credentials" "$OUT_DIR" \
    "$SIM_CTL" field-package "$SIM_STATE" "$PROFILE" "$VERSION"
fi

STATUS="pass"
if [[ "$FAILURES" -gt 0 ]]; then
  STATUS="fail"
fi
DEVICE_READINESS="needs-fix"
if [[ "$SIMULATE_DEVICE" -eq 1 && "$STATUS" == "pass" ]]; then
  DEVICE_READINESS="simulated-pass"
fi

{
  printf '{\n'
  printf '  "status": "%s",\n' "$STATUS"
  printf '  "steps": %s,\n' "$STEP"
  printf '  "failures": %s,\n' "$FAILURES"
  printf '  "warnings": %s,\n' "$WARNINGS"
  printf '  "simulate_device": %s,\n' "$SIMULATE_DEVICE"
  printf '  "device_readiness": "%s",\n' "$DEVICE_READINESS"
  printf '  "evidence": "%s",\n' "$EVIDENCE_MD"
  printf '  "logs": "%s"\n' "$LOG_DIR"
  printf '}\n'
} > "$SUMMARY_JSON"

{
  echo
  echo "## Summary"
  echo
  echo "- status: ${STATUS}"
  echo "- steps: ${STEP}"
  echo "- failures: ${FAILURES}"
  echo "- warnings: ${WARNINGS}"
  echo "- simulate_device: ${SIMULATE_DEVICE}"
  echo "- device_readiness: ${DEVICE_READINESS}"
  if [[ "$DEVICE_READINESS" == "simulated-pass" ]]; then
    echo "- hardware_readiness: not-claimed"
  fi
  echo "- summary_json: ${SUMMARY_JSON}"
} >> "$EVIDENCE_MD"

echo "[INFO] evidence=$EVIDENCE_MD"
echo "[INFO] summary=$SUMMARY_JSON"
echo "[INFO] status=$STATUS steps=$STEP failures=$FAILURES warnings=$WARNINGS"

[[ "$STATUS" == "pass" ]]
