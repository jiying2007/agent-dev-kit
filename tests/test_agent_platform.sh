#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export ADK_ROOT="$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

run_json() {
  local out="$1"
  shift
  bash "$ROOT/scripts/devkit.sh" platform "$@" >"$out"
}

run_json "$TMP/maturity.json" maturity
python3 - "$TMP/maturity.json" <<'PY'
import json, sys
v=json.load(open(sys.argv[1], encoding='utf-8'))
assert v['status']=='pass'
assert v['product_qualification']['adk_self_certifies'] is False
assert v['component_release_maturity']['current']=='release-candidate'
assert v['runtime_conformance_ladder'][-1]=='runtime-certified'
PY

run_json "$TMP/resolve.json" resolve --profile core --target claude-code --project-capability embedded --session-capability review
python3 - "$TMP/resolve.json" <<'PY'
import json, sys
v=json.load(open(sys.argv[1], encoding='utf-8'))
assert v['status']=='pass'
assert v['schema']=='adk-effective-profile/v1'
assert v['target']=='claude-code'
assert v['resolution_sha256']
assert set(v['effective_capabilities'])=={'embedded','review'}
PY

run_json "$TMP/skills.json" portable-skills
python3 - "$TMP/skills.json" <<'PY'
import json, sys
v=json.load(open(sys.argv[1], encoding='utf-8'))
assert v['status']=='pass', v
assert v['checked_skills'] > 10
assert v['failures']==[]
PY

cat >"$TMP/trace.json" <<'JSON'
{
  "schema": "adk-agent-trace/v1",
  "trace_id": "trace-1",
  "runtime": {"name": "fixture", "version": "1", "requested_model": null, "actual_served_model": null},
  "started_at": "2026-09-12T00:00:00Z",
  "completed_at": "2026-09-12T00:00:01Z",
  "result": "pass",
  "privacy": {"raw_prompts_stored": false, "secrets_stored": false, "sanitized": true},
  "spans": [
    {
      "span_id": "span-1",
      "parent_span_id": null,
      "kind": "run",
      "name": "fixture",
      "agent": null,
      "skill": null,
      "tool_schema_digest": null,
      "started_at": "2026-09-12T00:00:00Z",
      "duration_ms": 1,
      "input_context_bytes": 0,
      "output_tokens": 0,
      "side_effect_class": "none",
      "approval": "not-applicable",
      "result": "pass",
      "evidence_digest": null
    }
  ]
}
JSON
run_json "$TMP/trace-result.json" trace-validate --input "$TMP/trace.json"
grep -q '"status":"pass"' "$TMP/trace-result.json"

cat >"$TMP/verifier.json" <<'JSON'
{
  "schema": "adk-independent-verifier-receipt/v1",
  "receipt_id": "verify-1",
  "builder_context_id": "builder-1",
  "verifier_context_id": "verifier-1",
  "verifier_write_capability": false,
  "evidence_opened": true,
  "verification_target_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "verdict": "pass",
  "verified_at": "2026-09-12T00:00:00Z",
  "evidence_digests": []
}
JSON
run_json "$TMP/verifier-result.json" verifier-validate --input "$TMP/verifier.json"
grep -q '"status":"pass"' "$TMP/verifier-result.json"
python3 - "$TMP/verifier.json" "$TMP/verifier-bad.json" <<'PY'
import json, sys
v=json.load(open(sys.argv[1], encoding='utf-8'))
v['verifier_context_id']=v['builder_context_id']
json.dump(v, open(sys.argv[2], 'w', encoding='utf-8'))
PY
if bash "$ROOT/scripts/devkit.sh" platform verifier-validate --input "$TMP/verifier-bad.json" >/dev/null; then
  echo '[FAIL] same-context verifier unexpectedly passed' >&2
  exit 1
fi

run_json "$TMP/loop.json" loop-decision --iterations 12 --wall-time-seconds 1 --cost-usd 0 --tokens 1 --consecutive-no-progress 0
python3 - "$TMP/loop.json" <<'PY'
import json, sys
v=json.load(open(sys.argv[1], encoding='utf-8'))
assert v['decision']=='stop-needs-evidence'
assert 'iteration-budget' in v['reasons']
assert v['fresh_context_required'] is True
PY
run_json "$TMP/loop-pass.json" loop-decision --iterations 1 --wall-time-seconds 1 --cost-usd 0 --tokens 1 --consecutive-no-progress 0 --evaluator-pass
grep -q '"decision":"complete"' "$TMP/loop-pass.json"

cat >"$TMP/aci.json" <<'JSON'
{
  "context_amplification_ratio": 2.0,
  "irrelevant_output_ratio": 0.1,
  "tool_recovery_rate": 0.95,
  "empty_result_ambiguity_rate": 0.01,
  "syntax_error_prevention_rate": 0.9,
  "search_precision": 0.8,
  "repeated_call_rate": 0.1
}
JSON
run_json "$TMP/aci-result.json" aci --metrics "$TMP/aci.json"
grep -q '"status":"pass"' "$TMP/aci-result.json"

run_json "$TMP/usage.json" asset-usage
python3 - "$TMP/usage.json" <<'PY'
import json, sys
v=json.load(open(sys.argv[1], encoding='utf-8'))
assert v['status']=='not-measured'
assert v['auto_archive_allowed'] is False
assert len(v['assets']) > 10
PY

run_json "$TMP/hooks.json" hooks
python3 - "$TMP/hooks.json" <<'PY'
import json, sys
v=json.load(open(sys.argv[1], encoding='utf-8'))
assert list(v['events']['before_tool'].values()) == ['PreToolUse']
assert 'hidden-workflow-orchestration' in v['forbidden_effects']
PY

run_json "$TMP/conformance-plan.json" target-conformance --target claude-code --profile core
python3 - "$TMP/conformance-plan.json" <<'PY'
import json, sys
v=json.load(open(sys.argv[1], encoding='utf-8'))
assert v['status']=='ready'
assert v['certification']=='not-certified'
assert len(v['stages'])==13
assert v['stages'][0]['stage']=='render'
assert v['stages'][-1]['stage']=='rollback'
PY

python3 - "$TMP/commands.json" <<'PY'
import json, sys
stages=['render','install','discovery','load','positive-trigger','negative-trigger','permission','tool-invocation','handoff','cancel','resume','trace','rollback']
json.dump({'commands': {stage: ['/bin/true'] for stage in stages}}, open(sys.argv[1], 'w', encoding='utf-8'))
PY
run_json "$TMP/conformance-run.json" target-conformance --target claude-code --profile core --commands "$TMP/commands.json"
python3 - "$TMP/conformance-run.json" <<'PY'
import json, sys
v=json.load(open(sys.argv[1], encoding='utf-8'))
assert v['status']=='pass'
assert v['certification']=='caller-supplied-full-smoke'
assert v['conformance_level']=='behavior-evaluated'
assert v['native_runtime_certified'] is False
assert len(v['results'])==13
PY

[[ ! -e "$ROOT/scripts/platform-vnext.sh" ]] || { echo '[FAIL] retired platform-vnext.sh returned' >&2; exit 1; }

echo '[PASS] stable Agent Platform primitives and fail-closed evidence semantics'
