#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PILOT_INDEX="${ROOT}/docs/pilots/index.tsv"
SUMMARY_JSON=0
PILOT_FILTER=""

usage() {
  cat <<USAGE
usage: scripts/pilot-readiness.sh [--pilot <pilot_id>] [--summary-json] [--list]

Checks pilot evidence readiness:
  - pilot index schema, status values and readiness dimensions
  - pilot evidence files exist and mirror indexed status
  - planned pilots keep pending evidence explicit
  - evidence-ready/regression-ready pilots include verification evidence

Options:
  --pilot <pilot_id>  Check one pilot.
  --summary-json     Print compact JSON summary.
  --list             List all pilots (default behavior).
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pilot)
      PILOT_FILTER="$2"
      shift 2
      ;;
    --summary-json)
      SUMMARY_JSON=1
      shift
      ;;
    --list)
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unknown arg: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

log() {
  [[ "${SUMMARY_JSON}" -eq 1 ]] && return 0
  echo "$1"
}

require_heading() {
  local file="$1"
  local heading="$2"
  rg -q "^${heading}$" "${file}" || fail "pilot file missing heading '${heading}': ${file#$ROOT/}"
}

[[ -f "${PILOT_INDEX}" ]] || fail "pilot index missing: ${PILOT_INDEX}"

expected_pilot_header=$'pilot_id\tstatus\tcapability\tprimary_skill\tfallback_used\tevidence_file\tverification\tworkflow_readiness\tartifact_readiness\tdevice_readiness\treadiness_note'
actual_pilot_header="$(head -n 1 "${PILOT_INDEX}")"
[[ "${actual_pilot_header}" == "${expected_pilot_header}" ]] || fail "pilot index header mismatch"

valid_pilot_statuses=" planned evidence-ready regression-ready rejected "
valid_readiness_values=" pass partial pending needs-fix simulated-pass not-applicable "
pilots=0
ready=0
planned=0
rejected=0
device_needs_fix=0
device_simulated_pass=0
found=0

while IFS=$'\t' read -r pilot_id status capability primary_skill fallback_used evidence_file verification workflow_readiness artifact_readiness device_readiness readiness_note; do
  [[ -n "${pilot_id}" ]] || continue
  if [[ -n "${PILOT_FILTER}" && "${pilot_id}" != "${PILOT_FILTER}" ]]; then
    continue
  fi
  found=1
  pilots=$((pilots + 1))

  [[ "${valid_pilot_statuses}" == *" ${status} "* ]] || fail "invalid pilot status for ${pilot_id}: ${status}"
  [[ -n "${capability}" && -n "${primary_skill}" ]] || fail "pilot row incomplete: ${pilot_id}"
  [[ "${fallback_used}" == "yes" || "${fallback_used}" == "no" ]] || fail "invalid fallback_used for ${pilot_id}: ${fallback_used}"
  [[ "${valid_readiness_values}" == *" ${workflow_readiness} "* ]] || fail "invalid workflow_readiness for ${pilot_id}: ${workflow_readiness}"
  [[ "${valid_readiness_values}" == *" ${artifact_readiness} "* ]] || fail "invalid artifact_readiness for ${pilot_id}: ${artifact_readiness}"
  [[ "${valid_readiness_values}" == *" ${device_readiness} "* ]] || fail "invalid device_readiness for ${pilot_id}: ${device_readiness}"
  [[ -n "${readiness_note}" && "${readiness_note}" != "-" ]] || fail "missing readiness_note for ${pilot_id}"
  [[ -f "${ROOT}/${evidence_file}" ]] || fail "pilot evidence file missing: ${evidence_file}"
  rg -q "^status: ${status}$" "${ROOT}/${evidence_file}" || fail "pilot file status mismatch for ${pilot_id}: ${evidence_file}"
  require_heading "${ROOT}/${evidence_file}" "## 目标场景"

  readiness="${status}"
  case "${status}" in
    planned)
      planned=$((planned + 1))
      require_heading "${ROOT}/${evidence_file}" "## 预期路由"
      require_heading "${ROOT}/${evidence_file}" "## 待补证据"
      ;;
    evidence-ready|regression-ready)
      ready=$((ready + 1))
      [[ "${verification}" != "pending" && "${verification}" != "-" ]] || fail "ready pilot requires verification: ${pilot_id}"
      require_heading "${ROOT}/${evidence_file}" "## 预期路由"
      require_heading "${ROOT}/${evidence_file}" "## 验证证据"
      ;;
    rejected)
      rejected=$((rejected + 1))
      ;;
  esac
  if [[ "${device_readiness}" == "needs-fix" ]]; then
    device_needs_fix=$((device_needs_fix + 1))
  fi
  if [[ "${device_readiness}" == "simulated-pass" ]]; then
    device_simulated_pass=$((device_simulated_pass + 1))
  fi

  log "[PILOT] ${pilot_id} status=${status} readiness=${readiness} workflow=${workflow_readiness} artifact=${artifact_readiness} device=${device_readiness} fallback_used=${fallback_used} evidence=${evidence_file} verification=${verification}"
done < <(tail -n +2 "${PILOT_INDEX}")

if [[ -n "${PILOT_FILTER}" && "${found}" -eq 0 ]]; then
  fail "pilot not found: ${PILOT_FILTER}"
fi
[[ "${pilots}" -gt 0 ]] || fail "pilot index has no rows"

if [[ "${SUMMARY_JSON}" -eq 1 ]]; then
  printf '{"status":"pass","pilots":%s,"ready":%s,"planned":%s,"rejected":%s,"device_needs_fix":%s,"device_simulated_pass":%s}\n' "${pilots}" "${ready}" "${planned}" "${rejected}" "${device_needs_fix}" "${device_simulated_pass}"
else
  echo "[INFO] pilot_readiness ready=${ready} planned=${planned} rejected=${rejected} device_needs_fix=${device_needs_fix} device_simulated_pass=${device_simulated_pass} total=${pilots}"
  echo "[PASS] pilot readiness checks passed (${pilots} pilots)"
fi
