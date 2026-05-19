#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PILOT_INDEX="${ROOT}/docs/pilots/index.tsv"
FALLBACK_MATRIX="${ROOT}/docs/reference/fallback-sunset-matrix.tsv"
SUMMARY_JSON=0
PILOT_FILTER=""

usage() {
  cat <<USAGE
usage: scripts/pilot-readiness.sh [--pilot <pilot_id>] [--summary-json] [--list]

Checks pilot evidence readiness:
  - pilot index schema and status values
  - pilot evidence files exist and mirror indexed status
  - planned pilots keep pending evidence explicit
  - evidence-ready/regression-ready pilots include verification evidence
  - fallback sunset matrix links are reported for each pilot

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

linked_fallbacks_for_file() {
  local evidence_file="$1"
  awk -F '\t' -v file="${evidence_file}" '
    NR == 1 {next}
    {
      split($9, refs, ",")
      for (i in refs) {
        if (refs[i] == file) {
          if (out != "") out = out ","
          out = out $1
        }
      }
    }
    END {
      if (out == "") print "-"
      else print out
    }
  ' "${FALLBACK_MATRIX}"
}

[[ -f "${PILOT_INDEX}" ]] || fail "pilot index missing: ${PILOT_INDEX}"
[[ -f "${FALLBACK_MATRIX}" ]] || fail "fallback matrix missing: ${FALLBACK_MATRIX}"

expected_pilot_header=$'pilot_id\tstatus\tcapability\tprimary_skill\tfallback_used\tevidence_file\tverification'
actual_pilot_header="$(head -n 1 "${PILOT_INDEX}")"
[[ "${actual_pilot_header}" == "${expected_pilot_header}" ]] || fail "pilot index header mismatch"

expected_fallback_header=$'fallback_skill\tadk_equivalent\tstatus\towner\treview_by\tlive_requirement\tnext_step\tmatch_text\tpilot_refs'
actual_fallback_header="$(head -n 1 "${FALLBACK_MATRIX}")"
[[ "${actual_fallback_header}" == "${expected_fallback_header}" ]] || fail "fallback matrix header mismatch"

valid_pilot_statuses=" planned evidence-ready regression-ready rejected "
pilots=0
ready=0
planned=0
rejected=0
found=0

while IFS=$'\t' read -r pilot_id status capability primary_skill fallback_used evidence_file verification; do
  [[ -n "${pilot_id}" ]] || continue
  if [[ -n "${PILOT_FILTER}" && "${pilot_id}" != "${PILOT_FILTER}" ]]; then
    continue
  fi
  found=1
  pilots=$((pilots + 1))

  [[ "${valid_pilot_statuses}" == *" ${status} "* ]] || fail "invalid pilot status for ${pilot_id}: ${status}"
  [[ -n "${capability}" && -n "${primary_skill}" ]] || fail "pilot row incomplete: ${pilot_id}"
  [[ "${fallback_used}" == "yes" || "${fallback_used}" == "no" ]] || fail "invalid fallback_used for ${pilot_id}: ${fallback_used}"
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

  linked_fallbacks="$(linked_fallbacks_for_file "${evidence_file}")"
  log "[PILOT] ${pilot_id} status=${status} readiness=${readiness} linked_fallbacks=${linked_fallbacks} evidence=${evidence_file} verification=${verification}"
done < <(tail -n +2 "${PILOT_INDEX}")

if [[ -n "${PILOT_FILTER}" && "${found}" -eq 0 ]]; then
  fail "pilot not found: ${PILOT_FILTER}"
fi
[[ "${pilots}" -gt 0 ]] || fail "pilot index has no rows"

if [[ "${SUMMARY_JSON}" -eq 1 ]]; then
  printf '{"status":"pass","pilots":%s,"ready":%s,"planned":%s,"rejected":%s}\n' "${pilots}" "${ready}" "${planned}" "${rejected}"
else
  echo "[INFO] pilot_readiness ready=${ready} planned=${planned} rejected=${rejected} total=${pilots}"
  echo "[PASS] pilot readiness checks passed (${pilots} pilots)"
fi
