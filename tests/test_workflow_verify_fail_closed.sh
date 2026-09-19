#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

mkdir -p "$TMP_DIR/scripts" "$TMP_DIR/changes/fail-closed"
cp "$ROOT_DIR/scripts/workflow.sh" "$TMP_DIR/scripts/workflow.sh"
cat >"$TMP_DIR/scripts/devkit.sh" <<'DEVKIT'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "validate" && "${2:-}" == "--strict" ]]; then
  echo "[FAIL] injected strict failure" >&2
  exit 23
fi
echo "[FAIL] unexpected devkit fixture invocation: $*" >&2
exit 2
DEVKIT
printf '%s\n' '#!/usr/bin/env bash' 'echo "[PASS] format must not run after strict failure"' >"$TMP_DIR/scripts/check-format.sh"
printf '%s\n' '#!/usr/bin/env bash' 'echo "[PASS] change fixture"' >"$TMP_DIR/scripts/check-change-governance.sh"
printf '%s\n' 'stage: applied' 'owner: fixture' 'updated_at: 2026-08-24T00:00:00Z' >"$TMP_DIR/changes/fail-closed/state.yaml"
chmod +x "$TMP_DIR/scripts/"*.sh

if "$TMP_DIR/scripts/workflow.sh" verify --change fail-closed --root "$TMP_DIR/changes" >/dev/null 2>&1; then
  echo "[FAIL] workflow verify swallowed an injected strict gate failure" >&2
  exit 1
fi
grep -q '^stage: verify-failed$' "$TMP_DIR/changes/fail-closed/state.yaml" || {
  echo "[FAIL] failed verify did not persist verify-failed state" >&2
  exit 1
}
grep -q 'injected strict failure' "$TMP_DIR/changes/fail-closed/verify-report.md" || {
  echo "[FAIL] verify report lost the first gate failure" >&2
  exit 1
}
if grep -q 'format must not run' "$TMP_DIR/changes/fail-closed/verify-report.md"; then
  echo "[FAIL] verify continued after the first failed gate" >&2
  exit 1
fi

echo "[PASS] workflow verify propagates the first failed sub-gate"
