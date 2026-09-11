#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$ROOT"

version="$(python - <<'PY'
import json
print(json.load(open('manifest.json', encoding='utf-8'))['version'])
PY
)"
head_sha="$(git rev-parse HEAD)"
tree_sha="$(git rev-parse 'HEAD^{tree}')"
manifest_blob="$(git hash-object manifest.json)"

cat > "$TMP/release-contract.json" <<JSON
{
  "schema": "adk-release-artifact-contract-set/v1",
  "status": "pass",
  "artifacts": [
    {
      "schema": "adk-release-artifact-contract/v1",
      "status": "pass",
      "version": "$version",
      "artifact": "agent-dev-kit-$version.tar.gz",
      "artifact_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "release_manifest_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "manifest_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "sbom_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "release_eligible": false
    }
  ]
}
JSON

python -m agent_dev_kit.distribution.promotion_evidence generate \
  --root "$ROOT" \
  --release-contract "$TMP/release-contract.json" \
  --out "$TMP/promotion-evidence.json" \
  --repository jiying2007/agent-dev-kit \
  --ref refs/heads/main \
  --event push \
  --workflow agent-dev-kit-ci \
  --workflow-ref 'jiying2007/agent-dev-kit/.github/workflows/ci.yml@refs/heads/main' \
  --workflow-sha "$head_sha" \
  --run-id 123 \
  --run-attempt 1 \
  --contract-result success \
  --regression-result success \
  --static-security-result success \
  --deterministic-result success

python -m agent_dev_kit.distribution.promotion_evidence validate "$TMP/promotion-evidence.json"

python - "$TMP/promotion-evidence.json" "$head_sha" "$tree_sha" "$manifest_blob" <<'PY'
import json, sys
path, head, tree, blob = sys.argv[1:]
value = json.load(open(path, encoding='utf-8'))
assert value['schema'] == 'adk-promotion-evidence/v1'
assert value['source']['commit'] == head
assert value['source']['tree'] == tree
assert value['source']['manifest_blob'] == blob
assert value['ci']['contract_matrix']['python'] == ['3.11', '3.12']
assert value['ci']['regression_matrix']['python'] == ['3.11', '3.12']
assert value['provenance']['subject'] == 'promotion-evidence.json'
PY

python - "$TMP/promotion-evidence.json" "$TMP/bad-ci.json" <<'PY'
import json, sys
src, dst = sys.argv[1:]
value = json.load(open(src, encoding='utf-8'))
value['ci']['static_security'] = 'failure'
json.dump(value, open(dst, 'w', encoding='utf-8'))
PY
if python -m agent_dev_kit.distribution.promotion_evidence validate "$TMP/bad-ci.json"; then
  echo '[FAIL] invalid CI claim unexpectedly validated' >&2
  exit 1
fi

python - "$TMP/promotion-evidence.json" "$TMP/bad-ref.json" <<'PY'
import json, sys
src, dst = sys.argv[1:]
value = json.load(open(src, encoding='utf-8'))
value['source']['ref'] = 'refs/pull/1/merge'
json.dump(value, open(dst, 'w', encoding='utf-8'))
PY
if python -m agent_dev_kit.distribution.promotion_evidence validate "$TMP/bad-ref.json"; then
  echo '[FAIL] non-main promotion evidence unexpectedly validated' >&2
  exit 1
fi

echo '[PASS] promotion evidence contract'
