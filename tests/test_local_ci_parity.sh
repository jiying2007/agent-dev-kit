#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="$ROOT_DIR/scripts/run-local-ci-parity.sh"
DOCKERFILE="$ROOT_DIR/tools/local-ci/Dockerfile"
ENTRYPOINT="$ROOT_DIR/tools/local-ci/entrypoint.sh"
WAIVER="$ROOT_DIR/docs/changes/adk-terminal-contract-hardening/ci-waiver.json"

for required in "$RUNNER" "$DOCKERFILE" "$ENTRYPOINT" "$WAIVER" "$ROOT_DIR/docs/runbooks/local-ci-parity.md"; do
  [[ -f "$required" ]] || {
    echo "[FAIL] local CI parity contract file is missing: $required" >&2
    exit 1
  }
done

plan="$(bash "$RUNNER" --python all --mode full --dry-run)"
for token in \
  'transport=docker' \
  'source_mount=read-only' \
  'work_copy=isolated-tmpfs' \
  'network=gates-none,audit-bridge,prepare-build-network' \
  'credentials=not-mounted' \
  'release_authority=none' \
  'file_mode_inventory=git-index-bound' \
  'container_user=65532:65532' \
  'python=3.11' \
  'python=3.12'; do
  rg -Fq -- "$token" <<<"$plan" || {
    echo "[FAIL] local CI dry-run omitted boundary: $token" >&2
    exit 1
  }
done

if bash "$RUNNER" --python 3.10 --dry-run >/dev/null 2>&1; then
  echo "[FAIL] local CI parity accepted an unsupported Python version" >&2
  exit 1
fi

for token in \
  '--read-only' \
  '--network none' \
  '--network bridge' \
  '--user 65532:65532' \
  '--cap-drop ALL' \
  'no-new-privileges' \
  '--tmpfs /work:rw,exec,nosuid,nodev,size=2g,mode=1777' \
  'dst=/source,readonly' \
  'python:3.11-slim@sha256:' \
  'python:3.12-slim@sha256:'; do
  rg -Fq -- "$token" "$RUNNER" || {
    echo "[FAIL] local CI runner omitted hardening token: $token" >&2
    exit 1
  }
done

[[ "$(rg -c -- '--network none' "$RUNNER")" == "1" ]] || {
  echo "[FAIL] local CI runner must have exactly one offline gates container" >&2
  exit 1
}
[[ "$(rg -c -- '--network bridge' "$RUNNER")" == "1" ]] || {
  echo "[FAIL] local CI runner must limit bridge to one dependency audit container" >&2
  exit 1
}
for token in \
  'ADK_LOCAL_CI_PHASE=gates' \
  'ADK_LOCAL_CI_PHASE=audit' \
  'io.agent-dev-kit.local-ci.definition-sha256' \
  'tool_image_id[$version]=' \
  'local CI image contract mismatch'; do
  rg -Fq -- "$token" "$RUNNER" || {
    echo "[FAIL] local CI runner omitted phase or image identity contract: $token" >&2
    exit 1
  }
done

for token in \
  'mktemp -d' \
  'source_snapshot_sha256=' \
  'file_mode_inventory_sha256=' \
  'sha256sum "$SNAPSHOT_TAR"' \
  'sha256sum "$MODE_INVENTORY"' \
  'src=$SNAPSHOT_SOURCE,dst=/source,readonly'; do
  rg -Fq -- "$token" "$RUNNER" || {
    echo "[FAIL] local CI runner omitted host snapshot boundary: $token" >&2
    exit 1
  }
done
rg -Fq -- 'ADK_FILE_MODE_INVENTORY=/inventory/file-modes.z' "$RUNNER"

for forbidden in 'docker.sock' '.ssh' 'git push' 'release publish' 'software-m5 certify'; do
  if rg -Fq -- "$forbidden" "$RUNNER" "$ENTRYPOINT"; then
    echo "[FAIL] local CI runner contains forbidden authority path: $forbidden" >&2
    exit 1
  fi
done

for excluded in '.git' '.ruff_cache' 'build' 'dist' '*.egg-info' '__pycache__'; do
  rg -Fq -- "$excluded" "$ENTRYPOINT" || {
    echo "[FAIL] local CI work copy omitted residue exclusion: $excluded" >&2
    exit 1
  }
done
rg -Fq -- '--no-same-owner' "$ENTRYPOINT"
rg -Fq -- 'chmod -R u=rwX,go=rX /work/source' "$ENTRYPOINT"
rg -Fq -- 'export TMPDIR=/work/tmp' "$ENTRYPOINT"
rg -Fq -- 'ADK_LOCAL_CI_PHASE' "$ENTRYPOINT"
rg -Fq -- 'io.agent-dev-kit.local-ci.contract="v2"' "$DOCKERFILE"
rg -Fq -- 'useradd --uid 65532 --gid 65532' "$DOCKERFILE"

for token in \
  'setuptools==${SETUPTOOLS_VERSION}' \
  'PyYAML==${PYYAML_VERSION}' \
  'jsonschema==${JSONSCHEMA_VERSION}' \
  'ruff==${RUFF_VERSION}' \
  'pip-audit==${PIP_AUDIT_VERSION}'; do
  rg -Fq -- "$token" "$DOCKERFILE" || {
    echo "[FAIL] local CI image omitted pinned dependency: $token" >&2
    exit 1
  }
done

python3 - "$WAIVER" <<'PY'
import datetime as dt
import json
import sys

waiver = json.load(open(sys.argv[1], encoding="utf-8"))
assert waiver["schema_version"] == "adk-ci-continuation-waiver/v1", waiver
assert waiver["effect"] == "local-development-continuation-only", waiver
assert waiver["authorized_by"] == "user", waiver
issued = dt.date.fromisoformat(waiver["authorized_at"])
expires = dt.date.fromisoformat(waiver["expires_at"])
assert dt.timedelta(0) < expires - issued <= dt.timedelta(days=7), waiver
assert set(waiver["scope"]["allow"]) == {"local-development", "local-test", "local-review"}, waiver
denied = set(waiver["scope"]["deny"])
for required in {
    "remote-ci-pass-claim",
    "release",
    "publish",
    "tag",
    "software-m5-certification",
    "field-evidence",
    "source-to-live",
}:
    assert required in denied, (required, waiver)
assert waiver["transport"]["source_mount"] == "host-snapshot-read-only", waiver
assert waiver["transport"]["credentials"] == "not-mounted", waiver
assert waiver["alternative_evidence"]["status"] in {"pending", "pass", "fail"}, waiver
PY

echo "Local CI parity contract tests passed"
