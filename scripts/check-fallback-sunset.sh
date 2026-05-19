#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MATRIX="${ROOT}/docs/reference/fallback-sunset-matrix.tsv"
PILOT_INDEX="${ROOT}/docs/pilots/index.tsv"
SCORE_TSV=""
CANDIDATE_TSV=""
SUMMARY_JSON=0

usage() {
  cat <<USAGE
usage: scripts/check-fallback-sunset.sh [--score-tsv <path>] [--candidate-tsv <path>] [--summary-json]

Checks fallback sunset readiness:
  - matrix schema and status transitions
  - match_text routes to an expected adk_equivalent skill
  - candidate-sunset/sunset rows reference ready pilot evidence
  - active-fallback rows have owner, next_step and non-expired review_by
  - status-specific replacement score thresholds stay above the sunset gate
  - pilot index, readiness dimensions and pilot files stay in sync

Options:
  --score-tsv <path>  Write machine-readable replacement score rows.
  --candidate-tsv <path>
                      Write machine-readable sunset candidate queue rows.
  --summary-json     Print compact JSON summary instead of verbose rows.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --score-tsv)
      SCORE_TSV="$2"
      shift 2
      ;;
    --candidate-tsv)
      CANDIDATE_TSV="$2"
      shift 2
      ;;
    --summary-json)
      SUMMARY_JSON=1
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

[[ -f "${MATRIX}" ]] || fail "fallback matrix missing: ${MATRIX}"
[[ -f "${PILOT_INDEX}" ]] || fail "pilot index missing: ${PILOT_INDEX}"

expected_matrix_header=$'fallback_skill\tadk_equivalent\tstatus\towner\treview_by\tlive_requirement\tnext_step\tmatch_text\tpilot_refs'
actual_matrix_header="$(head -n 1 "${MATRIX}")"
[[ "${actual_matrix_header}" == "${expected_matrix_header}" ]] || fail "fallback matrix header mismatch"

expected_pilot_header=$'pilot_id\tstatus\tcapability\tprimary_skill\tfallback_used\tevidence_file\tverification\tworkflow_readiness\tartifact_readiness\tdevice_readiness\treadiness_note'
actual_pilot_header="$(head -n 1 "${PILOT_INDEX}")"
[[ "${actual_pilot_header}" == "${expected_pilot_header}" ]] || fail "pilot index header mismatch"

valid_statuses=" active-fallback explicit-fallback candidate-sunset sunset "
valid_live_requirements=" core-live-required optional-live-allowed handoff-ready-only "
valid_pilot_statuses=" planned evidence-ready regression-ready rejected "
valid_readiness_values=" pass partial pending needs-fix not-applicable "
rows=0
score_rows=0
score_total=0
threshold_failures=0
today="$(date +%F)"

skill_declared() {
  local skill="$1"
  [[ -f "${ROOT}/skills/${skill}/SKILL.md" ]] && return 0
  [[ -f "${ROOT}/optional-skills/${skill}/SKILL.md" ]] && return 0
  return 1
}

skill_optional() {
  local skill="$1"
  [[ -f "${ROOT}/optional-skills/${skill}/SKILL.md" ]]
}

skill_in_equivalent() {
  local skill="$1"
  local equivalent="$2"
  IFS='+' read -r -a skills <<< "${equivalent}"
  local item
  for item in "${skills[@]}"; do
    [[ "${skill}" == "${item}" ]] && return 0
  done
  return 1
}

extract_matched_skill() {
  local output="$1"
  awk '
    {
      for (i = 1; i <= NF; i++) {
        if ($i ~ /^skill=/) {
          value=$i
          sub(/^skill=/, "", value)
          print value
          exit
        }
      }
    }
  ' <<< "${output}"
}

pilot_status_for_file() {
  local file="$1"
  awk -F '\t' -v file="$file" '
    NR == 1 {next}
    $6 == file {print $2; found=1; exit}
    END {if (!found) exit 1}
  ' "${PILOT_INDEX}"
}

score_field() {
  local value="$1"
  if [[ "${value}" -eq 1 ]]; then
    printf "pass"
  else
    printf "gap"
  fi
}

status_threshold() {
  local status="$1"
  case "${status}" in
    active-fallback) printf "3" ;;
    explicit-fallback) printf "3" ;;
    candidate-sunset) printf "4" ;;
    sunset) printf "5" ;;
    *) fail "invalid status threshold lookup: ${status}" ;;
  esac
}

require_pilot_heading() {
  local file="$1"
  local heading="$2"
  rg -q "^${heading}$" "${file}" || fail "pilot file missing heading '${heading}': ${file#$ROOT/}"
}

if [[ -n "${SCORE_TSV}" ]]; then
  mkdir -p "$(dirname "${SCORE_TSV}")"
  printf "fallback_skill\tstatus\tmatched_skill\trouting\tprofile\tpilot\thandoff\tlive\tscore\tmax_score\n" > "${SCORE_TSV}"
fi

if [[ -n "${CANDIDATE_TSV}" ]]; then
  mkdir -p "$(dirname "${CANDIDATE_TSV}")"
  printf "fallback_skill\tcurrent_status\tmatched_skill\tscore\tlive\tcandidate_state\tnext_step\tpilot_refs\n" > "${CANDIDATE_TSV}"
fi

while IFS=$'\t' read -r fallback_skill adk_equivalent status owner review_by live_requirement next_step match_text pilot_refs; do
  [[ -n "${fallback_skill}" ]] || continue
  rows=$((rows + 1))

  [[ "${valid_statuses}" == *" ${status} "* ]] || fail "invalid status for ${fallback_skill}: ${status}"
  [[ "${valid_live_requirements}" == *" ${live_requirement} "* ]] || fail "invalid live_requirement for ${fallback_skill}: ${live_requirement}"
  [[ -n "${adk_equivalent}" && "${adk_equivalent}" != "-" ]] || fail "missing adk equivalent for ${fallback_skill}"
  [[ -n "${owner}" && "${owner}" != "-" ]] || fail "missing owner for ${fallback_skill}"
  [[ "${review_by}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || fail "invalid review_by for ${fallback_skill}: ${review_by}"
  [[ -n "${next_step}" && "${next_step}" != "-" ]] || fail "missing next_step for ${fallback_skill}"
  [[ -n "${match_text}" && "${match_text}" != "-" ]] || fail "missing match_text for ${fallback_skill}"

  if [[ "${status}" == "active-fallback" && "${review_by}" < "${today}" ]]; then
    fail "active fallback review_by expired for ${fallback_skill}: ${review_by}"
  fi

  match_output=""
  if ! match_output="$(bash "${ROOT}/scripts/devkit.sh" match --text "${match_text}" 2>&1)"; then
    echo "${match_output}" >&2
    fail "match_text did not route for ${fallback_skill}: ${match_text}"
  fi

  matched_skill="$(extract_matched_skill "${match_output}")"
  [[ -n "${matched_skill}" ]] || fail "could not parse matched skill for ${fallback_skill}: ${match_output}"
  if ! skill_in_equivalent "${matched_skill}" "${adk_equivalent}"; then
    echo "${match_output}" >&2
    fail "matched skill '${matched_skill}' is not in adk_equivalent for ${fallback_skill}: ${adk_equivalent}"
  fi

  routing_score=1
  profile_score=0
  if skill_declared "${matched_skill}"; then
    profile_score=1
  fi

  handoff_score="${profile_score}"
  live_score=0
  live_label="gap"
  if [[ -f "${HOME}/.codex/skills/${matched_skill}/SKILL.md" ]]; then
    live_score=1
    live_label="pass"
  elif [[ "${live_requirement}" == "optional-live-allowed" ]] && skill_optional "${matched_skill}" && [[ "${handoff_score}" -eq 1 ]]; then
    live_score=1
    live_label="optional-ok"
  elif [[ "${live_requirement}" == "handoff-ready-only" ]] && [[ "${handoff_score}" -eq 1 ]]; then
    live_score=1
    live_label="waived"
  fi

  pilot_score=0

  if [[ "${status}" == "candidate-sunset" || "${status}" == "sunset" ]]; then
    [[ -n "${pilot_refs}" && "${pilot_refs}" != "-" ]] || fail "${status} requires pilot refs for ${fallback_skill}"
  fi

  if [[ -n "${pilot_refs}" && "${pilot_refs}" != "-" ]]; then
    IFS=',' read -r -a refs <<< "${pilot_refs}"
    for ref in "${refs[@]}"; do
      [[ -f "${ROOT}/${ref}" ]] || fail "pilot ref missing for ${fallback_skill}: ${ref}"
      if ! rg -q --fixed-strings -- "${ref}" "${PILOT_INDEX}"; then
        fail "pilot ref not indexed for ${fallback_skill}: ${ref}"
      fi
      pilot_status="$(pilot_status_for_file "${ref}")" || fail "pilot ref has no status for ${fallback_skill}: ${ref}"
      if [[ "${status}" == "candidate-sunset" || "${status}" == "sunset" ]]; then
        if [[ "${pilot_status}" != "evidence-ready" && "${pilot_status}" != "regression-ready" ]]; then
          fail "${status} requires ready pilot for ${fallback_skill}: ${ref} status=${pilot_status}"
        fi
      fi
      if [[ "${pilot_status}" == "evidence-ready" || "${pilot_status}" == "regression-ready" ]]; then
        pilot_score=1
      fi
    done
  fi

  row_score=$((routing_score + profile_score + pilot_score + handoff_score + live_score))
  required_score="$(status_threshold "${status}")"
  if [[ "${row_score}" -lt "${required_score}" ]]; then
    threshold_failures=$((threshold_failures + 1))
    fail "${fallback_skill} score below ${status} threshold: score=${row_score}/5 required=${required_score}"
  fi
  score_rows=$((score_rows + 1))
  score_total=$((score_total + row_score))
  if [[ -n "${SCORE_TSV}" ]]; then
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t5\n" \
      "${fallback_skill}" \
      "${status}" \
      "${matched_skill}" \
      "$(score_field "${routing_score}")" \
      "$(score_field "${profile_score}")" \
      "$(score_field "${pilot_score}")" \
      "$(score_field "${handoff_score}")" \
      "${live_label}" \
      "${row_score}" >> "${SCORE_TSV}"
  fi
  if [[ -n "${CANDIDATE_TSV}" ]]; then
    candidate_state="not-ready"
    if [[ "${status}" == "sunset" ]]; then
      candidate_state="already-sunset"
    elif [[ "${status}" == "candidate-sunset" ]]; then
      candidate_state="candidate"
    elif [[ "${row_score}" -eq 5 ]]; then
      candidate_state="review-second-pilot-before-candidate"
    elif [[ "${row_score}" -eq 4 && "${live_score}" -eq 0 ]]; then
      candidate_state="live-gap"
    fi
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
      "${fallback_skill}" \
      "${status}" \
      "${matched_skill}" \
      "${row_score}/5" \
      "${live_label}" \
      "${candidate_state}" \
      "${next_step}" \
      "${pilot_refs:-}" >> "${CANDIDATE_TSV}"
  fi
  log "[SCORE] ${fallback_skill}=${row_score}/5 threshold=${required_score} routing=$(score_field "${routing_score}") profile=$(score_field "${profile_score}") pilot=$(score_field "${pilot_score}") handoff=$(score_field "${handoff_score}") live=${live_label} live_requirement=${live_requirement} matched=${matched_skill} status=${status}"
done < <(tail -n +2 "${MATRIX}")

[[ "${rows}" -gt 0 ]] || fail "fallback matrix has no rows"

while IFS=$'\t' read -r pilot_id status capability primary_skill fallback_used evidence_file verification workflow_readiness artifact_readiness device_readiness readiness_note; do
  [[ -n "${pilot_id}" ]] || continue
  [[ "${valid_pilot_statuses}" == *" ${status} "* ]] || fail "invalid pilot status for ${pilot_id}: ${status}"
  [[ -n "${status}" && -n "${capability}" && -n "${primary_skill}" ]] || fail "pilot row incomplete: ${pilot_id}"
  [[ "${fallback_used}" == "yes" || "${fallback_used}" == "no" ]] || fail "invalid fallback_used for ${pilot_id}: ${fallback_used}"
  [[ "${valid_readiness_values}" == *" ${workflow_readiness} "* ]] || fail "invalid workflow_readiness for ${pilot_id}: ${workflow_readiness}"
  [[ "${valid_readiness_values}" == *" ${artifact_readiness} "* ]] || fail "invalid artifact_readiness for ${pilot_id}: ${artifact_readiness}"
  [[ "${valid_readiness_values}" == *" ${device_readiness} "* ]] || fail "invalid device_readiness for ${pilot_id}: ${device_readiness}"
  [[ -n "${readiness_note}" && "${readiness_note}" != "-" ]] || fail "missing readiness_note for ${pilot_id}"
  [[ -f "${ROOT}/${evidence_file}" ]] || fail "pilot evidence file missing: ${evidence_file}"
  rg -q "^status: ${status}$" "${ROOT}/${evidence_file}" || fail "pilot file status mismatch for ${pilot_id}: ${evidence_file}"
  require_pilot_heading "${ROOT}/${evidence_file}" "## 目标场景"
  require_pilot_heading "${ROOT}/${evidence_file}" "## 预期路由"
  if [[ "${status}" == "evidence-ready" || "${status}" == "regression-ready" ]]; then
    [[ "${verification}" != "pending" && "${verification}" != "-" ]] || fail "ready pilot requires verification: ${pilot_id}"
    require_pilot_heading "${ROOT}/${evidence_file}" "## 验证证据"
  else
    require_pilot_heading "${ROOT}/${evidence_file}" "## 待补证据"
  fi
done < <(tail -n +2 "${PILOT_INDEX}")

max_score=$((score_rows * 5))
if [[ "${SUMMARY_JSON}" -eq 1 ]]; then
  printf '{"status":"pass","rows":%s,"replacement_score":%s,"max_score":%s,"threshold_failures":%s}\n' "${rows}" "${score_total}" "${max_score}" "${threshold_failures}"
else
  echo "[INFO] replacement_score=${score_total}/${max_score}"
  if [[ -n "${SCORE_TSV}" ]]; then
    echo "[INFO] score_tsv=${SCORE_TSV}"
  fi
  if [[ -n "${CANDIDATE_TSV}" ]]; then
    echo "[INFO] candidate_tsv=${CANDIDATE_TSV}"
  fi
  echo "[PASS] fallback sunset matrix checks passed (${rows} rows)"
fi
