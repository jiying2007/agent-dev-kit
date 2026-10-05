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

printf '100644 0000000000000000000000000000000000000000 0\tmissing.txt\0' >"$TMP_DIR/modes.z"
if "${ROOT_DIR}/scripts/check-file-modes.sh" "$TMP_DIR" --index-inventory "$TMP_DIR/modes.z" >/dev/null 2>&1; then
  echo "[FAIL] explicit file mode inventory accepted a missing file" >&2
  exit 1
fi

printf '100644 0000000000000000000000000000000000000000 0\t../escape\0' >"$TMP_DIR/modes.z"
if "${ROOT_DIR}/scripts/check-file-modes.sh" "$TMP_DIR" --index-inventory "$TMP_DIR/modes.z" >/dev/null 2>&1; then
  echo "[FAIL] file mode inventory accepted path traversal" >&2
  exit 1
fi

# All Git metadata and synthetic refs belong to this disposable fixture.
REPO="$TMP_DIR/repository"
WORKTREE="$TMP_DIR/worktree"
mkdir -p "$REPO" "$TMP_DIR/non-repository" "$TMP_DIR/bad-gitfile"
printf 'plain\n' >"$REPO/plain.txt"
printf '#!/bin/sh\nexit 0\n' >"$REPO/tool.sh"
chmod 644 "$REPO/plain.txt"
chmod 755 "$REPO/tool.sh"
git -C "$REPO" init -q
git -C "$REPO" add plain.txt tool.sh
git -C "$REPO" -c user.name=Fixture -c user.email=fixture@example.invalid \
  -c commit.gpgsign=false -c core.hooksPath=/dev/null \
  -c maintenance.autoDetach=false -c gc.autoDetach=false \
  commit -qm 'temporary file mode fixture'
git -C "$REPO" -c core.hooksPath=/dev/null worktree add --detach -q "$WORKTREE"
[[ -f "$WORKTREE/.git" ]] || { echo '[FAIL] fixture is not a linked worktree' >&2; exit 1; }

check_git_modes() {
  ADK_FILE_MODE_INVENTORY= "${ROOT_DIR}/scripts/check-file-modes.sh" "$@"
}

# Invoke from a cwd outside either Git fixture, including the default-root case.
(
  cd "$TMP_DIR/non-repository"
  "${ROOT_DIR}/scripts/check-file-modes.sh" >/dev/null
  check_git_modes "$REPO" >/dev/null
  check_git_modes "$WORKTREE" >/dev/null
)
chmod 755 "$WORKTREE/plain.txt"
chmod 644 "$WORKTREE/tool.sh"
if check_git_modes "$WORKTREE" >/dev/null 2>&1; then
  echo '[FAIL] linked worktree mode drift was accepted' >&2
  exit 1
fi
check_git_modes "$WORKTREE" --fix >/dev/null
check_git_modes "$WORKTREE" >/dev/null
[[ ! -x "$WORKTREE/plain.txt" && -x "$WORKTREE/tool.sh" ]] || {
  echo '[FAIL] linked worktree --fix did not restore index modes' >&2
  exit 1
}
rm "$WORKTREE/plain.txt"
check_git_modes "$WORKTREE" >/dev/null

mkdir -p "$REPO/nested"
printf 'gitdir: %s/missing-metadata\n' "$TMP_DIR" >"$TMP_DIR/bad-gitfile/.git"
for INVALID_ROOT in "$TMP_DIR/non-repository" "$REPO/nested" "$TMP_DIR/bad-gitfile"; do
  if check_git_modes "$INVALID_ROOT" >/dev/null 2>&1; then
    echo "[FAIL] invalid Git root was accepted: $INVALID_ROOT" >&2
    exit 1
  fi
done
