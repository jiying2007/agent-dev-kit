#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CHANGE_ROOT="$TMP_DIR/changes"
CHANGE_ID="smoke-change"
CHANGE_ID_ARTIFACT_FAIL="artifact-consistency-fail"
CHANGE_ID_ARTIFACT_PASS="artifact-consistency-pass"

fill_canonical_contract() {
  local change_id="$1"
  local proposal="$CHANGE_ROOT/$change_id/proposal.md"
  local tasks="$CHANGE_ROOT/$change_id/tasks.md"
  sed -i \
    -e "s/TBD requirement/$change_id requirement/" \
    -e "s/TBD target/$change_id target/" \
    -e "s/TBD surface/$change_id affected surface/" \
    -e "s/TBD acceptance criterion/$change_id acceptance criterion/" \
    "$proposal"
  sed -i "s/TBD implementation task/implement $change_id/" "$tasks"
}

fill_negative_results() {
  local change_id="$1"
  local file="$CHANGE_ROOT/$change_id/negative-results.md"
  cat > "$file" <<NEGATIVE
# 负结果记录：$change_id

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| T1 | 未补证据即可验证 | workflow verify smoke | 失败 | check-change-governance 需要真实负结果 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| workflow verify precheck | 1 | default template blocked before evidence fill | negative-results.md | Workflow | negative-results |
NEGATIVE
}

"$ROOT_DIR/scripts/workflow.sh" propose --change "$CHANGE_ID" --title "workflow smoke" --root "$CHANGE_ROOT"
[[ -f "$CHANGE_ROOT/$CHANGE_ID/negative-results.md" ]] || { echo "[FAIL] missing negative-results artifact" >&2; exit 1; }
grep -q "^## 问题陈述（单问题）" "$CHANGE_ROOT/$CHANGE_ID/proposal.md" || { echo "[FAIL] missing single-problem section" >&2; exit 1; }
grep -q "^## Spec 链路检查" "$CHANGE_ROOT/$CHANGE_ID/proposal.md" || { echo "[FAIL] missing spec-chain section" >&2; exit 1; }
grep -q "^## Canonical Change Contract" "$CHANGE_ROOT/$CHANGE_ID/proposal.md" || { echo "[FAIL] missing canonical change contract" >&2; exit 1; }
grep -q "REQ-001.*MODIFIED.*ACC-001.*TASK-001.*VERIFY-001" "$CHANGE_ROOT/$CHANGE_ID/proposal.md" || { echo "[FAIL] missing canonical traceability row" >&2; exit 1; }
grep -q "^## Ownership 与并行冲突检查" "$CHANGE_ROOT/$CHANGE_ID/tasks.md" || { echo "[FAIL] missing ownership section" >&2; exit 1; }
grep -q "^## 轻量工件与收敛结论" "$CHANGE_ROOT/$CHANGE_ID/tasks.md" || { echo "[FAIL] missing convergence section" >&2; exit 1; }
grep -q "TASK-001" "$CHANGE_ROOT/$CHANGE_ID/tasks.md" || { echo "[FAIL] missing canonical task id" >&2; exit 1; }
grep -q "^- \\[ \\] Prompt before/after 对比证据" "$CHANGE_ROOT/$CHANGE_ID/checklist.md" || { echo "[FAIL] missing prompt regression checklist item" >&2; exit 1; }
grep -q "^- \\[ \\] Evidence Index 命令级字段完整（命令/退出码/结果摘要/证据路径/层级/关联工件）" "$CHANGE_ROOT/$CHANGE_ID/checklist.md" || { echo "[FAIL] missing evidence index checklist item" >&2; exit 1; }
grep -q "^- \\[ \\] Canonical Change Contract 追溯关系完整" "$CHANGE_ROOT/$CHANGE_ID/checklist.md" || { echo "[FAIL] missing canonical contract checklist item" >&2; exit 1; }
grep -q "^## Evidence Index（命令级）" "$CHANGE_ROOT/$CHANGE_ID/negative-results.md" || { echo "[FAIL] missing command evidence index section" >&2; exit 1; }
grep -q "^| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |" "$CHANGE_ROOT/$CHANGE_ID/negative-results.md" || { echo "[FAIL] missing command evidence index table header" >&2; exit 1; }

if "$ROOT_DIR/scripts/workflow.sh" review --change "$CHANGE_ID" --root "$CHANGE_ROOT" --result pass --blockers 0 --majors 0 --minors 0 >/dev/null 2>&1; then
  echo "[FAIL] review should fail before verify stage" >&2
  exit 1
fi

"$ROOT_DIR/scripts/workflow.sh" apply --change "$CHANGE_ID" --root "$CHANGE_ROOT"
if "$ROOT_DIR/scripts/workflow.sh" archive --change "$CHANGE_ID" --root "$CHANGE_ROOT" >/dev/null 2>&1; then
  echo "[FAIL] archive should fail before review pass" >&2
  exit 1
fi

if "$ROOT_DIR/scripts/workflow.sh" verify --change "$CHANGE_ID" --root "$CHANGE_ROOT" >/dev/null 2>&1; then
  echo "[FAIL] verify should fail before canonical contract and negative evidence are complete" >&2
  exit 1
fi
grep -q '^stage: verify-failed$' "$CHANGE_ROOT/$CHANGE_ID/state.yaml" || {
  echo "[FAIL] failed verify did not enter retryable verify-failed stage" >&2
  exit 1
}
fill_canonical_contract "$CHANGE_ID"
fill_negative_results "$CHANGE_ID"
"$ROOT_DIR/scripts/workflow.sh" verify --change "$CHANGE_ID" --root "$CHANGE_ROOT"
grep -q 'VERIFY-001' "$CHANGE_ROOT/$CHANGE_ID/verify-report.md" || { echo "[FAIL] verify report missing contract verification id" >&2; exit 1; }
"$ROOT_DIR/scripts/workflow.sh" review --change "$CHANGE_ID" --root "$CHANGE_ROOT" --result pass --blockers 0 --majors 0 --minors 1
"$ROOT_DIR/scripts/workflow.sh" archive --change "$CHANGE_ID" --root "$CHANGE_ROOT"

ARCHIVE_MATCH="$(find "$CHANGE_ROOT/archive" -maxdepth 1 -type d -name "*-smoke-change" | head -n 1 || true)"
[[ -n "$ARCHIVE_MATCH" ]] || { echo "[FAIL] archive directory not found" >&2; exit 1; }
[[ -f "$ARCHIVE_MATCH/provenance.md" ]] || { echo "[FAIL] archive provenance missing" >&2; exit 1; }
grep -q '^stage: archived$' "$ARCHIVE_MATCH/state.yaml" || { echo "[FAIL] archive did not persist archived stage" >&2; exit 1; }
grep -q 'schema: adk-change-provenance/v1' "$ARCHIVE_MATCH/provenance.md" || { echo "[FAIL] archive provenance schema missing" >&2; exit 1; }
grep -q 'authority: ADK Canonical Change Contract' "$ARCHIVE_MATCH/provenance.md" || { echo "[FAIL] archive provenance authority missing" >&2; exit 1; }
grep -q 'promotion_authority: adk-promotion-evidence/v1' "$ARCHIVE_MATCH/provenance.md" || { echo "[FAIL] archive provenance promotion authority missing" >&2; exit 1; }

## artifact consistency checks - fail path
"$ROOT_DIR/scripts/workflow.sh" propose --change "$CHANGE_ID_ARTIFACT_FAIL" --title "artifact consistency fail" --root "$CHANGE_ROOT"
"$ROOT_DIR/scripts/workflow.sh" apply --change "$CHANGE_ID_ARTIFACT_FAIL" --root "$CHANGE_ROOT"
fill_canonical_contract "$CHANGE_ID_ARTIFACT_FAIL"
fill_negative_results "$CHANGE_ID_ARTIFACT_FAIL"

cat >> "$CHANGE_ROOT/$CHANGE_ID_ARTIFACT_FAIL/design.md" <<'ARTIFACTS'

[artifact:ReviewReport]
status: PASS
owner: tester
verdict: pass

[artifact:TestReport]
status: PASS
owner: tester
tests_run:
- fake test result
ARTIFACTS

"$ROOT_DIR/scripts/workflow.sh" verify --change "$CHANGE_ID_ARTIFACT_FAIL" --root "$CHANGE_ROOT"

if "$ROOT_DIR/scripts/workflow.sh" review --change "$CHANGE_ID_ARTIFACT_FAIL" --root "$CHANGE_ROOT" --result needs-fix --blockers 0 --majors 0 --minors 1 >/dev/null 2>&1; then
  echo "[FAIL] review should fail when result conflicts with artifact PASS/PASS" >&2
  exit 1
fi

## artifact consistency checks - pass path
"$ROOT_DIR/scripts/workflow.sh" propose --change "$CHANGE_ID_ARTIFACT_PASS" --title "artifact consistency pass" --root "$CHANGE_ROOT"
"$ROOT_DIR/scripts/workflow.sh" apply --change "$CHANGE_ID_ARTIFACT_PASS" --root "$CHANGE_ROOT"
fill_canonical_contract "$CHANGE_ID_ARTIFACT_PASS"
fill_negative_results "$CHANGE_ID_ARTIFACT_PASS"

cat >> "$CHANGE_ROOT/$CHANGE_ID_ARTIFACT_PASS/design.md" <<'ARTIFACTS'

[artifact:ReviewReport]
status: PASS
owner: tester
verdict: pass

[artifact:TestReport]
status: PASS
owner: tester
tests_run:
- fake test result
ARTIFACTS

"$ROOT_DIR/scripts/workflow.sh" verify --change "$CHANGE_ID_ARTIFACT_PASS" --root "$CHANGE_ROOT"
"$ROOT_DIR/scripts/workflow.sh" review --change "$CHANGE_ID_ARTIFACT_PASS" --root "$CHANGE_ROOT" --result pass --blockers 0 --majors 0 --minors 1

echo "[PASS] workflow"
