#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=./lib_manifest.sh
source "$SCRIPT_DIR/lib_manifest.sh"

usage() {
  cat <<USAGE
Usage:
  ./scripts/check_profile_coherence.sh

Checks:
  - profile extends must not redeclare inherited agents/skills
  - profile direct includes must not contain duplicate entries
  - profile references must point to manifest-declared agents/skills
  - default_profile must exist
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "[FAIL] unexpected arguments: $*" >&2
  usage >&2
  exit 1
fi

adk_require_manifest

manifest_contains() {
  local section="$1"
  local name="$2"
  adk_list_manifest_names "$section" | grep -Fxq "$name"
}

check_direct_duplicates() {
  local profile="$1"
  local key="$2"
  local duplicates

  duplicates="$(adk_get_profile_list "$profile" "$key" | awk '
    NF {
      seen[$0]++
    }
    END {
      for (item in seen) {
        if (seen[item] > 1) {
          print item
        }
      }
    }
  ')"

  if [[ -n "$duplicates" ]]; then
    while IFS= read -r item; do
      [[ -z "$item" ]] && continue
      echo "[FAIL] profile ${profile} duplicates ${key}: ${item}" >&2
    done <<< "$duplicates"
    return 1
  fi
}

check_inherited_redeclaration() {
  local profile="$1"
  local key="$2"
  local parents parent item inherited
  local failed=0

  parents="$(adk_get_profile_list "$profile" "extends")"
  [[ -n "$parents" ]] || return 0

  inherited="$(mktemp)"
  while IFS= read -r parent; do
    [[ -z "$parent" ]] && continue
    if ! adk_profile_exists "$parent"; then
      echo "[FAIL] profile ${profile} extends unknown profile: ${parent}" >&2
      failed=1
      continue
    fi
    adk_collect_profile_items "$parent" "$key" "" >> "$inherited"
  done <<< "$parents"

  sort -u "$inherited" -o "$inherited"
  while IFS= read -r item; do
    [[ -z "$item" ]] && continue
    if grep -Fxq "$item" "$inherited"; then
      echo "[FAIL] profile ${profile} redeclares inherited ${key}: ${item}" >&2
      failed=1
    fi
  done < <(adk_get_profile_list "$profile" "$key")

  rm -f "$inherited"
  return "$failed"
}

check_manifest_references() {
  local profile="$1"
  local key="$2"
  local section="$3"
  local item failed=0

  while IFS= read -r item; do
    [[ -z "$item" ]] && continue
    if ! manifest_contains "$section" "$item"; then
      echo "[FAIL] profile ${profile} references unknown ${key}: ${item}" >&2
      failed=1
    fi
  done < <(adk_get_profile_list "$profile" "$key")

  return "$failed"
}

# === Profile 冲突检测 ===
check_profile_conflicts() {
  local manifest="$1"
  local conflicts_found=0
  local current_profile=""

  # 解析 manifest，找到带 conflicts_with 的 profile
  while IFS= read -r line; do
    # 匹配 profile 名称行（2空格缩进 + kebab-case 名称 + 冒号）
    if [[ "$line" =~ ^\ \ ([a-z][a-z0-9-]+):$ ]]; then
      current_profile="${BASH_REMATCH[1]}"
    fi
    # 匹配 conflicts_with 字段
    if [[ "$line" =~ conflicts_with:\ \[(.+)\] ]]; then
      local conflicts="${BASH_REMATCH[1]}"
      for conflict in ${conflicts//,/ }; do
        conflict=$(echo "$conflict" | tr -d " ")
        if [[ -n "$conflict" ]]; then
          echo "[WARN] Profile '$current_profile' conflicts with '$conflict'"
          conflicts_found=$((conflicts_found + 1))
        fi
      done
    fi
  done < "$manifest"

  return $conflicts_found
}


failed=0
default_profile="$(awk '/^default_profile:/ {print $2; exit}' "$ADK_MANIFEST")"
if [[ -z "$default_profile" ]] || ! adk_profile_exists "$default_profile"; then
  echo "[FAIL] default_profile is missing or unknown: ${default_profile:-<empty>}" >&2
  failed=1
fi

while IFS= read -r profile; do
  [[ -z "$profile" ]] && continue
  if [[ -z "$(adk_get_profile_value "$profile" "description")" ]]; then
    echo "[FAIL] profile ${profile} missing description" >&2
    failed=1
  fi

  check_direct_duplicates "$profile" "include_agents" || failed=1
  check_direct_duplicates "$profile" "include_skills" || failed=1
  check_inherited_redeclaration "$profile" "include_agents" || failed=1
  check_inherited_redeclaration "$profile" "include_skills" || failed=1
  check_manifest_references "$profile" "include_agents" "agents" || failed=1
  check_manifest_references "$profile" "include_skills" "skills" || failed=1
done < <(adk_list_profile_names)

# 检测 profile 冲突
check_profile_conflicts "$ADK_MANIFEST" || true

if [[ "$failed" -ne 0 ]]; then
  echo "[FAIL] profile coherence checks failed" >&2
  exit 1
fi

echo "[PASS] profile coherence checks passed"
