#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

"${ROOT_DIR}/scripts/check-file-modes.sh" "${ROOT_DIR}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
printf 'fixture\n' >"$TMP_DIR/file.txt"
printf '100644 0000000000000000000000000000000000000000 0\tfile.txt\0' >"$TMP_DIR/modes.z"
"${ROOT_DIR}/scripts/check-file-modes.sh" "$TMP_DIR" --index-inventory "$TMP_DIR/modes.z" >/dev/null

chmod 755 "$TMP_DIR/file.txt"
if "${ROOT_DIR}/scripts/check-file-modes.sh" "$TMP_DIR" --index-inventory "$TMP_DIR/modes.z" >/dev/null 2>&1; then
  echo "[FAIL] file mode inventory accepted unexpected executable bit" >&2
  exit 1
fi
if "${ROOT_DIR}/scripts/check-file-modes.sh" "$TMP_DIR" --index-inventory "$TMP_DIR/modes.z" --fix >/dev/null 2>&1; then
  echo "[FAIL] file mode inventory accepted --fix" >&2
  exit 1
fi

printf '100644 0000000000000000000000000000000000000000 0\t../escape\0' >"$TMP_DIR/modes.z"
if "${ROOT_DIR}/scripts/check-file-modes.sh" "$TMP_DIR" --index-inventory "$TMP_DIR/modes.z" >/dev/null 2>&1; then
  echo "[FAIL] file mode inventory accepted path traversal" >&2
  exit 1
fi
