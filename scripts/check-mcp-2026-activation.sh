#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FIXTURE_DIR="$ROOT_DIR/tests/mcp_2026_activation"
MANIFEST="$ROOT_DIR/manifests/skill_mcp_dependencies.json"

IMAGE="docker.io/library/golang:1.25.1-bookworm@sha256:c423747fbd96fd8f0b1102d947f51f9b266060217478e5f9bf86f145969562ee"
SDK_MODULE="github.com/modelcontextprotocol/go-sdk"
SDK_VERSION="v1.7.0-pre.3"
CACHE_ROOT="${MCP_2026_CACHE_ROOT:-/tmp/adk-mcp-2026-activation-cache}"
GO_PATH="$CACHE_ROOT/go-path"
BUILD_CACHE="$CACHE_ROOT/go-build"
REPORT_PATH="${MCP_2026_REPORT_PATH:-/tmp/adk-mcp-2026-activation-go-test.jsonl}"

usage() {
  cat <<'EOF'
Usage:
  check-mcp-2026-activation.sh --prepare
  check-mcp-2026-activation.sh --offline

Modes:
  --prepare  Download go.sum-pinned modules into an explicit /tmp cache.
  --offline  Run the four version-pinned smokes with Docker --network=none,
             then require the manifest owner-decision and activation state.

Environment:
  MCP_2026_CACHE_ROOT   Explicit cache root (default: /tmp/adk-mcp-2026-activation-cache)
  MCP_2026_REPORT_PATH  Go test JSONL report (default: /tmp/adk-mcp-2026-activation-go-test.jsonl)
EOF
}

if [[ $# -eq 1 && ( "$1" == "--help" || "$1" == "-h" ) ]]; then
  usage
  exit 0
fi

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

mode="$1"
if [[ "$mode" != "--prepare" && "$mode" != "--offline" ]]; then
  usage >&2
  exit 2
fi

command -v docker >/dev/null 2>&1 || {
  echo "[FAIL] docker is required for the pinned MCP activation fixture" >&2
  exit 1
}

docker image inspect "$IMAGE" >/dev/null

if ! rg -q --fixed-strings "require $SDK_MODULE $SDK_VERSION" "$FIXTURE_DIR/go.mod"; then
  echo "[FAIL] go.mod does not pin $SDK_MODULE $SDK_VERSION" >&2
  exit 1
fi

mkdir -p "$GO_PATH" "$BUILD_CACHE" "$BUILD_CACHE/tmp"

if [[ "$mode" == "--prepare" ]]; then
  docker run --rm \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    -e GOPATH=/gopath \
    -e GOMODCACHE=/gopath/pkg/mod \
    -e GOCACHE=/gocache \
    -e GOTMPDIR=/gocache/tmp \
    -e GOFLAGS=-mod=readonly \
    -v "$FIXTURE_DIR:/workspace:ro" \
    -v "$GO_PATH:/gopath" \
    -v "$BUILD_CACHE:/gocache" \
    -w /workspace \
    "$IMAGE" \
    go mod download
  echo "[PASS] prepared pinned MCP modules in $GO_PATH"
  exit 0
fi

if [[ ! -f "$FIXTURE_DIR/go.sum" ]]; then
  echo "[FAIL] missing go.sum; generate and review it before offline verification" >&2
  exit 1
fi

docker run --rm \
  --network=none \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -e GOPATH=/gopath \
  -e GOMODCACHE=/gopath/pkg/mod \
  -e GOCACHE=/gocache \
  -e GOTMPDIR=/gocache/tmp \
  -e GOFLAGS=-mod=readonly \
  -v "$FIXTURE_DIR:/workspace:ro" \
  -v "$GO_PATH:/gopath:ro" \
  -v "$BUILD_CACHE:/gocache" \
  -w /workspace \
  "$IMAGE" \
  go test -count=1 -json ./... | tee "$REPORT_PATH"

python3 - "$MANIFEST" "$SDK_MODULE" "$SDK_VERSION" "$IMAGE" <<'PY'
import json
import sys
from pathlib import Path

manifest_path, sdk_module, sdk_version, image = sys.argv[1:]
manifest_file = Path(manifest_path)
root = manifest_file.parent.parent
data = json.loads(manifest_file.read_text(encoding="utf-8"))
policy = data["protocol_compatibility_policy"]
candidate = policy["candidates"][0]
gate = policy["activation_gate"]

assert policy["active_protocol_version"] == "2026-07-28"
assert policy["active_scope"] == "protocol-governance-contract-only"
assert policy["active_runtime_enabled"] is False
assert policy["active_feature_enablement"] == {
    "tasks": False,
    "apps": False,
    "extensions": False,
}
assert candidate["protocol_version"] == "2026-07-28"
assert candidate["runtime_enabled"] is False
assert candidate["feature_enablement"] == {
    "tasks": False,
    "apps": False,
    "extensions": False,
}
assert candidate["final_compatibility_claim"] is True
evidence = candidate["compatibility_evidence"]
assert evidence["sdk_module"] == sdk_module
assert evidence["sdk_version"] == sdk_version
assert evidence["runtime_image"] == image
assert evidence["network_mode"] == "offline-container-loopback-only"
for field in (
    "schema_fixture_completed",
    "client_server_smoke_completed",
    "auth_security_review_completed",
    "rollback_smoke_completed",
):
    assert gate[field] is True
assert gate["owner_decision_required"] is True
assert gate["owner_decision_completed"] is True
assert gate["owner_decision_id"] == "mcp-act-2026-07-31-leiwenjun"
assert gate["activation_allowed"] is True
assert gate["activation_completed"] is True
assert gate["activation_scope"] == "protocol-governance-contract-only"
assert gate["rollback_target_protocol_version"] == "2025-11-25"

decision = json.loads((root / gate["owner_decision_path"]).read_text(encoding="utf-8"))
assert decision["decision_id"] == gate["owner_decision_id"]
assert decision["candidate_id"] == "epc-c6f947d482aa8aa0c78f"
assert decision["protocol_version"] == policy["active_protocol_version"]
assert decision["decision"] == "ACTIVATE"
assert decision["owner"] == "leiwenjun"
assert decision["scope"] == policy["active_scope"]
assert decision["runtime_enabled"] is False
assert decision["feature_enablement"] == policy["active_feature_enablement"]
PY

echo "[PASS] MCP 2026 governance-contract activation fixture"
