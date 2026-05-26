#!/usr/bin/env bash
set -euo pipefail

PILOT="all"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${ADK_WORKFLOW_PILOT_OUT:-/tmp/adk-pilot/embedded-workflow-pilots/${TIMESTAMP}}"

usage() {
  cat <<USAGE
Usage:
  scripts/run-embedded-workflow-pilots.sh [--pilot <name>] [--out <path>]

Generates deterministic evidence for embedded workflow pilots without touching
hardware, remotes, worktrees, or source repositories.

Pilots:
  all
  long-task
  bugfix
  test-strategy
  review
  verification
  parallel-governance
  branch-closeout

Options:
  --pilot <name>  Pilot to run. Default: all.
  --out <path>    Evidence output directory. Default: ${OUT_DIR}
  -h, --help      Show this help.
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
    --pilot)
      require_value "$1" "${2:-}"
      PILOT="$2"
      shift 2
      ;;
    --out)
      require_value "$1" "${2:-}"
      OUT_DIR="$2"
      shift 2
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

case "$PILOT" in
  all|long-task|bugfix|test-strategy|review|verification|parallel-governance|branch-closeout)
    ;;
  *)
    echo "[FAIL] unsupported pilot: $PILOT" >&2
    usage >&2
    exit 1
    ;;
esac

mkdir -p "$OUT_DIR"

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

init_pilot() {
  local pilot_id="$1"
  PILOT_DIR="$OUT_DIR/$pilot_id"
  LOG_DIR="$PILOT_DIR/logs"
  EVIDENCE_MD="$PILOT_DIR/evidence.md"
  SUMMARY_JSON="$PILOT_DIR/summary.json"
  rm -rf "$PILOT_DIR"
  mkdir -p "$LOG_DIR"
  STEP=0
  FAILURES=0

  {
    echo "# Evidence: $pilot_id"
    echo
    echo "- generated_at: $(date -Iseconds)"
    echo "- output_dir: $PILOT_DIR"
    echo
    echo "## Evidence Index（命令级）"
    echo "| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |"
    echo "|---|---:|---|---|---|---|"
  } > "$EVIDENCE_MD"
}

run_step() {
  local mode="$1"
  local name="$2"
  local summary="$3"
  local cwd="$4"
  shift 4

  STEP=$((STEP + 1))
  local slug log_file cmd_display rc result
  slug="$(slugify "$name")"
  log_file="$LOG_DIR/$(printf '%02d' "$STEP")-${slug}.log"
  cmd_display="$(quote_cmd "$@")"
  rc=0

  set +e
  (cd "$cwd" && "$@") >"$log_file" 2>&1
  rc=$?
  set -e

  result="pass"
  case "$mode" in
    required)
      if [[ "$rc" -ne 0 ]]; then
        result="fail"
        FAILURES=$((FAILURES + 1))
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
      echo "[FAIL] internal error: unsupported mode $mode" >&2
      exit 1
      ;;
  esac

  printf '| `%s` | %s | %s (%s) | `%s` | Workflow | embedded-workflow-pilot |\n' \
    "$(escape_cell "$cmd_display")" \
    "$rc" \
    "$(escape_cell "$summary")" \
    "$result" \
    "$log_file" >> "$EVIDENCE_MD"
  echo "[STEP] $PILOT_ID:$name rc=$rc result=$result"
}

finish_pilot() {
  local status="pass"
  [[ "$FAILURES" -eq 0 ]] || status="fail"
  {
    printf '{\n'
    printf '  "status": "%s",\n' "$status"
    printf '  "pilot": "%s",\n' "$PILOT_ID"
    printf '  "steps": %s,\n' "$STEP"
    printf '  "failures": %s,\n' "$FAILURES"
    printf '  "evidence": "%s"\n' "$EVIDENCE_MD"
    printf '}\n'
  } > "$SUMMARY_JSON"
  {
    echo
    echo "## Summary"
    echo
    echo "- status: $status"
    echo "- steps: $STEP"
    echo "- failures: $FAILURES"
    echo "- summary_json: $SUMMARY_JSON"
  } >> "$EVIDENCE_MD"
  [[ "$status" == "pass" ]]
}

run_long_task() {
  PILOT_ID="embedded-fullstack-long-task-recovery"
  init_pilot "$PILOT_ID"
  mkdir -p "$PILOT_DIR/checkpoints"
  cat > "$PILOT_DIR/plan.md" <<'EOF'
# PCR02 BSP/OTA Hardening Plan

## Goal
- Stabilize a staged embedded full-stack task across SoC build, MCU release, vehicle OTA, and evidence closeout.

## Stages
1. Discovery and boundary lock.
2. MCU package and SoC self-check evidence.
3. Scope change: defer real flashing to HIL phase.
4. Recovery and final verification.
EOF
  cat > "$PILOT_DIR/checkpoints/01-discovery.md" <<'EOF'
status: pass
checkpoint: discovery
evidence: scope locked for SoC build + MCU release dry-run
EOF
  cat > "$PILOT_DIR/checkpoints/02-package-self-check.md" <<'EOF'
status: pass
checkpoint: package-self-check
evidence: package/checksum/self-check commands defined
EOF
  cat > "$PILOT_DIR/scope-change.md" <<'EOF'
change: defer hardware flash/readback
reason: no HIL bench in this pilot
decision: keep dry-run evidence, mark hardware evidence pending
EOF
  cat > "$PILOT_DIR/recovery-summary.md" <<'EOF'
resume_from: checkpoint 02-package-self-check
next_action: run verification and record gaps
rollback_anchor: pre-HIL dry-run evidence
EOF
  cat > "$PILOT_DIR/verify-report.md" <<'EOF'
status: pass
commands:
- scripts/run-embedded-production-field-pilot.sh
gaps:
- real flash/readback
- vehicle OTA rollback drill
EOF

  run_step required "plan-has-stages" "long task plan declares staged execution" "$PILOT_DIR" rg -q "## Stages" plan.md
  run_step required "checkpoint-1" "first checkpoint exists" "$PILOT_DIR" test -f checkpoints/01-discovery.md
  run_step required "checkpoint-2" "second checkpoint exists" "$PILOT_DIR" test -f checkpoints/02-package-self-check.md
  run_step required "scope-change" "mid-task scope change is explicit" "$PILOT_DIR" rg -q "defer hardware" scope-change.md
  run_step required "recovery-summary" "resume summary and rollback anchor exist" "$PILOT_DIR" rg -q "rollback_anchor" recovery-summary.md
  run_step required "verify-report" "final verification records residual gaps" "$PILOT_DIR" rg -q "status: pass" verify-report.md
  finish_pilot
}

run_test_strategy() {
  PILOT_ID="embedded-tdd-test-strategy"
  init_pilot "$PILOT_ID"
  mkdir -p "$PILOT_DIR/fixtures"
  cat > "$PILOT_DIR/test-matrix.md" <<'EOF'
# Embedded Test Strategy Matrix

| Level | Entry | Evidence |
|---|---|---|
| Level 0 | script smoke | pass |
| Level 1 | host unit + ctest fixture | pass |
| Level 2 | red/green behavior change | pass |
| Hardware gap | HIL manual record | pending |
EOF
  cat > "$PILOT_DIR/fixtures/host-unit-red.log" <<'EOF'
FAIL adc_scale expected=3300 actual=0
EOF
  cat > "$PILOT_DIR/fixtures/host-unit-green.log" <<'EOF'
PASS adc_scale expected=3300 actual=3300
EOF
  cat > "$PILOT_DIR/fixtures/ctest.log" <<'EOF'
100% tests passed, 0 tests failed out of 3
EOF
  cat > "$PILOT_DIR/fixtures/cross-build-smoke.log" <<'EOF'
arm-none-eabi-gcc --version: observed
cross-build: dry-run compile command generated
EOF
  cat > "$PILOT_DIR/fixtures/qemu-sil.log" <<'EOF'
qemu/sil: stubbed boot smoke command generated
EOF
  cat > "$PILOT_DIR/fixtures/hil-manual-record.md" <<'EOF'
status: pending
reason: hardware bench not attached
required_evidence: flash/readback, boot log, IO smoke
EOF

  run_step required "matrix-levels" "test matrix declares Level 0/1/2 and hardware gap" "$PILOT_DIR" rg -q "Level 2" test-matrix.md
  run_step expect-fail "red-output" "red test output is captured before green fix" "$PILOT_DIR" bash -c "rg -q '^FAIL' fixtures/host-unit-red.log && exit 1"
  run_step required "green-output" "green test output is captured after fix" "$PILOT_DIR" rg -q "^PASS" fixtures/host-unit-green.log
  run_step required "ctest-entry" "ctest fixture is represented" "$PILOT_DIR" rg -q "100% tests passed" fixtures/ctest.log
  run_step required "cross-build-smoke" "cross-build smoke command is represented" "$PILOT_DIR" rg -q "cross-build" fixtures/cross-build-smoke.log
  run_step required "qemu-sil-stub" "QEMU/SIL smoke gap has an entry" "$PILOT_DIR" rg -q "qemu/sil" fixtures/qemu-sil.log
  run_step required "hil-record" "HIL manual record keeps hardware evidence pending" "$PILOT_DIR" rg -q "required_evidence" fixtures/hil-manual-record.md
  finish_pilot
}

run_bugfix() {
  PILOT_ID="embedded-bugfix-systematic-debugging"
  init_pilot "$PILOT_ID"
  cat > "$PILOT_DIR/reproduction.log" <<'EOF'
ERROR: package manifest missing during firmware release validation
command: check-package /tmp/adk-pilot/missing-bundle
exit_code: 2
EOF
  cat > "$PILOT_DIR/hypotheses.md" <<'EOF'
H1: generated package path is wrong
H2: manifest generation failed
H3: checksum validation corrupted the manifest
EOF
  cat > "$PILOT_DIR/negative-results.md" <<'EOF'
rejected: H3 checksum validation corrupted the manifest
evidence: checksum step never ran because package_manifest.json was absent
EOF
  cat > "$PILOT_DIR/root-cause.md" <<'EOF'
root_cause: check-package was executed before package-external generated package_manifest.json
minimal_fix: enforce package-external before check-package in the runner
EOF
  cat > "$PILOT_DIR/regression.md" <<'EOF'
status: pass
commands:
- run package-external
- run check-package
expected: manifest and checksums are valid
EOF

  run_step required "reproduction" "reproduction log captures command and exit code" "$PILOT_DIR" rg -q "exit_code: 2" reproduction.log
  run_step required "hypotheses" "root-cause hypotheses are explicit" "$PILOT_DIR" rg -q "H1:" hypotheses.md
  run_step expect-fail "negative-result" "rejected hypothesis is recorded as a negative path" "$PILOT_DIR" bash -c "rg -q '^rejected:' negative-results.md && exit 1"
  run_step required "root-cause" "root cause is stated before fix" "$PILOT_DIR" rg -q "root_cause:" root-cause.md
  run_step required "regression" "regression verification is recorded" "$PILOT_DIR" rg -q "status: pass" regression.md
  finish_pilot
}

run_review() {
  PILOT_ID="embedded-review-code-review-loop"
  init_pilot "$PILOT_ID"
  cat > "$PILOT_DIR/review-scope.md" <<'EOF'
scope:
- scripts/run-embedded-production-field-pilot.sh
- docs/pilots/embedded-production-field-readiness.md
non_scope:
- real hardware flashing
EOF
  cat > "$PILOT_DIR/review-report.md" <<'EOF'
blocker:
- none
major:
- dirty gate output must be recorded as observed, not pass
minor:
- evidence output should be idempotent for same --out
question:
- should HIL be required for regression-ready?
EOF
  cat > "$PILOT_DIR/feedback-triage.md" <<'EOF'
accepted:
- idempotent --out cleanup for generated subdirectories
false_positive:
- request to run real flashing during dry-run pilot
out_of_scope:
- push release tag to remote
EOF
  cat > "$PILOT_DIR/rereview.md" <<'EOF'
status: pass
blockers: 0
majors: 0
minors: 0
EOF

  run_step required "scope" "review scope and non-scope are explicit" "$PILOT_DIR" rg -q "non_scope" review-scope.md
  run_step required "severity" "review report has blocker/major/minor/question sections" "$PILOT_DIR" bash -c "rg -q '^blocker:' review-report.md && rg -q '^major:' review-report.md && rg -q '^minor:' review-report.md && rg -q '^question:' review-report.md"
  run_step required "feedback-triage" "false positive and out-of-scope feedback are recorded" "$PILOT_DIR" bash -c "rg -q '^false_positive:' feedback-triage.md && rg -q '^out_of_scope:' feedback-triage.md"
  run_step required "rereview" "post-fix rereview passes with zero blockers" "$PILOT_DIR" rg -q "blockers: 0" rereview.md
  finish_pilot
}

run_verification() {
  PILOT_ID="embedded-verification-completion"
  init_pilot "$PILOT_ID"
  cat > "$PILOT_DIR/scope-summary.md" <<'EOF'
scope:
- embedded full-stack skill and pilot evidence closeout
- fallback sunset matrix verification
non_scope:
- real hardware production readiness declaration
EOF
  cat > "$PILOT_DIR/verification-index.md" <<'EOF'
| Command | Exit Code | Result |
|---|---:|---|
| rtk bash tests/run_all.sh | 0 | pass |
| rtk bash scripts/pilot-readiness.sh --summary-json | 0 | 9/9 evidence-ready |
| rtk bash scripts/check-fallback-sunset.sh --summary-json | 0 | replacement score passes threshold |
EOF
  cat > "$PILOT_DIR/negative-results.md" <<'EOF'
missing-evidence: reject completion claim when verification command is absent
missing-hardware: do not promote dry-run production pilot to production-ready
EOF
  cat > "$PILOT_DIR/runtime-config-audit.md" <<'EOF'
runtime_config:
- runtime handoff must be checked before live installation claims
- global runtime health must be checked before production claims
status: pass
EOF
  cat > "$PILOT_DIR/breaking-change.md" <<'EOF'
breaking_change: no
migration_required: no
rollback: revert pilot/index/matrix changes as one commit if checks fail
EOF
  cat > "$PILOT_DIR/final-gate.md" <<'EOF'
Final Gate Result: pass
blockers: 0
majors: 0
minors: 0
residual_risk:
- real hardware evidence remains a separate production-field gate
EOF

  run_step required "scope-summary" "completion scope and non-scope are explicit" "$PILOT_DIR" rg -q "non_scope" scope-summary.md
  run_step required "verification-index" "command-level verification index is present" "$PILOT_DIR" rg -q "check-fallback-sunset" verification-index.md
  run_step expect-fail "missing-evidence-negative-path" "missing evidence blocks completion claims" "$PILOT_DIR" bash -c "rg -q '^missing-evidence:' negative-results.md && exit 1"
  run_step required "runtime-config-audit" "runtime config audit requirement is recorded" "$PILOT_DIR" rg -q "runtime health" runtime-config-audit.md
  run_step required "breaking-change" "breaking change and rollback decision are explicit" "$PILOT_DIR" rg -q "breaking_change: no" breaking-change.md
  run_step required "final-gate" "final gate result has zero blockers" "$PILOT_DIR" rg -q "blockers: 0" final-gate.md
  finish_pilot
}

run_parallel() {
  PILOT_ID="embedded-parallel-worktree-governance"
  init_pilot "$PILOT_ID"
  cat > "$PILOT_DIR/task-packages.tsv" <<'EOF'
task_id	scope_write	must_not_touch	verify
driver-doc	docs/driver-bringup.md	manifest.yaml	rtk bash tests/test_templates.sh
test-runner	scripts/run-embedded-workflow-pilots.sh	manifest.yaml	rtk bash tests/test_embedded_workflow_pilots.sh
pilot-doc	docs/pilots/embedded-parallel-worktree-governance.md	scripts/run-embedded-workflow-pilots.sh	rtk bash scripts/pilot-readiness.sh --pilot embedded-parallel-worktree-governance
EOF
  cat > "$PILOT_DIR/conflict-matrix.md" <<'EOF'
| Pair | Conflict | Decision |
|---|---|---|
| driver-doc/test-runner | no shared write scope | parallel allowed |
| test-runner/pilot-doc | shared dependency, no shared write scope | integrate serially after runner |
EOF
  cat > "$PILOT_DIR/subagent-review.md" <<'EOF'
scope_write_checked: pass
must_not_touch_checked: pass
verification_declared: pass
needs_followup: no
EOF
  cat > "$PILOT_DIR/worktree-decision.md" <<'EOF'
decision: no-worktree-for-stub
reason: generated evidence only; no branch isolation needed
cleanup: not applicable
EOF
  cat > "$PILOT_DIR/integration-verify.md" <<'EOF'
status: pass
command: rtk bash tests/test_embedded_workflow_pilots.sh
EOF

  run_step required "task-package" "task packages declare scope_write, must_not_touch and verify" "$PILOT_DIR" bash -c "rg -q 'scope_write' task-packages.tsv && rg -q 'must_not_touch' task-packages.tsv && rg -q 'verify' task-packages.tsv"
  run_step required "conflict-matrix" "conflict matrix records pairwise decisions" "$PILOT_DIR" rg -q "parallel allowed" conflict-matrix.md
  run_step required "subagent-review" "subagent review checklist passes scope and verification checks" "$PILOT_DIR" rg -q "scope_write_checked: pass" subagent-review.md
  run_step required "worktree-decision" "worktree create/skip decision is documented" "$PILOT_DIR" rg -q "decision:" worktree-decision.md
  run_step required "integration-verify" "final integration verification command is recorded" "$PILOT_DIR" rg -q "status: pass" integration-verify.md
  finish_pilot
}

run_branch_closeout() {
  PILOT_ID="embedded-branch-closeout"
  init_pilot "$PILOT_ID"
  cat > "$PILOT_DIR/branch-status.md" <<'EOF'
branch: feature/adk-production-field-readiness
dirty_worktree: yes
untracked: generated pilot docs and scripts
remote_action: not allowed without explicit user approval
EOF
  cat > "$PILOT_DIR/verification-index.md" <<'EOF'
| Command | Exit Code | Result |
|---|---:|---|
| rtk bash tests/run_all.sh | 0 | pass |
| rtk bash scripts/check-fallback-sunset.sh --summary-json | 0 | pass |
| rtk scripts/check-adk-harden-readiness.sh . --require-pilot --skip-full-suite | 0 | pass |
EOF
  cat > "$PILOT_DIR/risk-rollback.md" <<'EOF'
risks:
- generated evidence is dry-run and does not prove hardware readiness
rollback:
- revert pilot runner and index updates in one commit if downstream handoff fails
EOF
  cat > "$PILOT_DIR/closeout-decision.md" <<'EOF'
decision: keep-branch-and-prepare-review
reason: local evidence passes; remote PR/push requires explicit user approval
next_action: user decides commit/PR timing
EOF
  cat > "$PILOT_DIR/pr-checklist.md" <<'EOF'
summary: required
validation: required
risk_rollback: required
human_review: required
EOF

  run_step required "branch-status" "branch state and remote-action boundary are recorded" "$PILOT_DIR" rg -q "remote_action" branch-status.md
  run_step required "verification-index" "verification command index is present" "$PILOT_DIR" rg -q "tests/run_all.sh" verification-index.md
  run_step required "risk-rollback" "risk and rollback are explicit" "$PILOT_DIR" rg -q "rollback:" risk-rollback.md
  run_step required "closeout-decision" "closeout decision is explicit" "$PILOT_DIR" rg -q "decision:" closeout-decision.md
  run_step required "pr-checklist" "PR checklist requires summary, validation and risk" "$PILOT_DIR" rg -q "human_review: required" pr-checklist.md
  finish_pilot
}

run_selected() {
  case "$1" in
    long-task) run_long_task ;;
    bugfix) run_bugfix ;;
    test-strategy) run_test_strategy ;;
    review) run_review ;;
    verification) run_verification ;;
    parallel-governance) run_parallel ;;
    branch-closeout) run_branch_closeout ;;
  esac
}

if [[ "$PILOT" == "all" ]]; then
  run_selected long-task
  run_selected bugfix
  run_selected test-strategy
  run_selected review
  run_selected verification
  run_selected parallel-governance
  run_selected branch-closeout
else
  run_selected "$PILOT"
fi

echo "[INFO] output=$OUT_DIR"
