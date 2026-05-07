#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<USAGE
Usage:
  ./scripts/openspec_bridge.sh <import|export|status-map> [options]

Options:
  --change <change-id>           # kebab-case, import/export 必填
  --openspec-root <path>         # 默认: \$PWD/openspec
  --gdk-root <path>              # 默认: <repo>/docs/changes
  --from-archive                 # import: 从 openspec/changes/archive/*-<change-id> 导入
  --archive-date <YYYY-MM-DD>    # export: 导出到 archive/<date>-<change-id>
  --stage <proposed|applied|verified|review-passed|archived> # import 时覆盖推断阶段
  -h, --help

Examples:
  ./scripts/openspec_bridge.sh import --change add-dark-mode --openspec-root /repo/openspec
  ./scripts/openspec_bridge.sh import --change add-dark-mode --from-archive --openspec-root /repo/openspec
  ./scripts/openspec_bridge.sh export --change add-dark-mode --openspec-root /repo/openspec
  ./scripts/openspec_bridge.sh export --change add-dark-mode --archive-date 2026-05-02 --openspec-root /repo/openspec
USAGE
}

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

ensure_kebab_change_id() {
  local value="$1"
  [[ -n "$value" ]] || fail "--change is required"
  [[ "$value" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || fail "--change must be kebab-case: $value"
}

ensure_stage_value() {
  local value="$1"
  case "$value" in
    proposed|applied|verified|review-passed|archived)
      ;;
    *)
      fail "invalid --stage: $value"
      ;;
  esac
}

ensure_archive_date() {
  local value="$1"
  [[ "$value" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || fail "invalid --archive-date: $value"
}

copy_file_if_exists() {
  local src="$1"
  local dst="$2"
  [[ -f "$src" ]] || return 0
  cp "$src" "$dst"
}

write_default_design_if_missing() {
  local file="$1"
  [[ -f "$file" ]] && return 0
  cat > "$file" <<'DESIGN'
# 设计说明

## 架构影响
- 待补充：从 OpenSpec 导入时原始变更未提供 design.md。

## 数据与配置影响
- 待补充。

## 兼容性与迁移方案
- 待补充。

## 验证策略
- 待补充。
DESIGN
}

write_default_checklist_if_missing() {
  local file="$1"
  [[ -f "$file" ]] && return 0
  cat > "$file" <<'CHECKLIST'
# 交付清单

- [ ] 关键场景覆盖
- [ ] 风险项评估完成
- [ ] 回退方案可执行
- [ ] 验证证据可追溯
- [ ] 评审结果为 pass（无 blocker/major 未闭环）
CHECKLIST
}

write_default_negative_results_if_missing() {
  local file="$1"
  [[ -f "$file" ]] && return 0
  cat > "$file" <<'NEGATIVE'
# 负结果记录

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| T0 | 待补充 | 待补充 | 待补充 | 待补充 |
NEGATIVE
}

infer_stage_from_openspec() {
  local src_dir="$1"
  local tasks_file="$2"

  if [[ "$src_dir" == *"/archive/"* ]]; then
    echo "archived"
    return 0
  fi

  if [[ -f "$tasks_file" ]] && rg -q '^- \[ \]' "$tasks_file"; then
    echo "proposed"
    return 0
  fi

  echo "applied"
}

write_state_and_history() {
  local target_dir="$1"
  local stage="$2"

  cat > "$target_dir/state.yaml" <<STATE
stage: $stage
owner: openspec-bridge
updated_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
notes: imported-from-openspec
STATE

printf '%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$stage" "openspec-bridge" > "$target_dir/history.log"
}

import_change() {
  local src_dir=""
  local target_dir="$GDK_ROOT/$CHANGE_ID"
  local stage="$STAGE_OVERRIDE"
  local archive_base="$OPENSPEC_ROOT/changes/archive"

  if [[ "$FROM_ARCHIVE" -eq 1 ]]; then
    [[ -d "$archive_base" ]] || fail "archive directory missing: $archive_base"
    src_dir="$(find "$archive_base" -maxdepth 1 -type d -name "*-$CHANGE_ID" | sort | tail -n 1 || true)"
    [[ -n "$src_dir" ]] || fail "archive change not found: *-$CHANGE_ID"
  else
    src_dir="$OPENSPEC_ROOT/changes/$CHANGE_ID"
    [[ -d "$src_dir" ]] || fail "active change not found: $src_dir"
  fi

  [[ ! -e "$target_dir" ]] || fail "target already exists: $target_dir"

  [[ -f "$src_dir/proposal.md" ]] || fail "missing proposal.md in openspec change: $src_dir"
  [[ -f "$src_dir/tasks.md" ]] || fail "missing tasks.md in openspec change: $src_dir"

  mkdir -p "$target_dir"
  cp "$src_dir/proposal.md" "$target_dir/proposal.md"
  cp "$src_dir/tasks.md" "$target_dir/tasks.md"
  copy_file_if_exists "$src_dir/design.md" "$target_dir/design.md"
  write_default_design_if_missing "$target_dir/design.md"

  if [[ -d "$src_dir/specs" ]]; then
    cp -R "$src_dir/specs" "$target_dir/specs"
  fi

  write_default_checklist_if_missing "$target_dir/checklist.md"
  write_default_negative_results_if_missing "$target_dir/negative-results.md"

  if [[ -z "$stage" ]]; then
    stage="$(infer_stage_from_openspec "$src_dir" "$src_dir/tasks.md")"
  fi
  ensure_stage_value "$stage"

  write_state_and_history "$target_dir" "$stage"

  echo "[OK] imported change: $CHANGE_ID"
  echo "[INFO] from=$src_dir"
  echo "[INFO] to=$target_dir"
  echo "[INFO] stage=$stage"
}

write_bridge_meta() {
  local dest_dir="$1"
  local stage="$2"

  cat > "$dest_dir/.openspec-bridge.yaml" <<META
source: agent-dev-kit
change_id: $CHANGE_ID
gdk_change_root: $GDK_ROOT
gdk_stage: $stage
exported_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
META
}

export_change() {
  local src_dir="$GDK_ROOT/$CHANGE_ID"
  local dest_dir=""
  local stage=""

  [[ -d "$src_dir" ]] || fail "gdk change not found: $src_dir"
  [[ -f "$src_dir/proposal.md" ]] || fail "missing gdk proposal.md: $src_dir"
  [[ -f "$src_dir/tasks.md" ]] || fail "missing gdk tasks.md: $src_dir"
  [[ -f "$src_dir/design.md" ]] || fail "missing gdk design.md: $src_dir"

  stage="$(awk '/^stage:/ {print $2; exit}' "$src_dir/state.yaml" 2>/dev/null || true)"
  [[ -n "$stage" ]] || stage="unknown"

  if [[ -n "$ARCHIVE_DATE" ]]; then
    ensure_archive_date "$ARCHIVE_DATE"
    dest_dir="$OPENSPEC_ROOT/changes/archive/$ARCHIVE_DATE-$CHANGE_ID"
  else
    dest_dir="$OPENSPEC_ROOT/changes/$CHANGE_ID"
  fi

  [[ ! -e "$dest_dir" ]] || fail "openspec target already exists: $dest_dir"

  mkdir -p "$dest_dir"
  cp "$src_dir/proposal.md" "$dest_dir/proposal.md"
  cp "$src_dir/design.md" "$dest_dir/design.md"
  cp "$src_dir/tasks.md" "$dest_dir/tasks.md"

  if [[ -d "$src_dir/specs" ]]; then
    cp -R "$src_dir/specs" "$dest_dir/specs"
  fi

  copy_file_if_exists "$src_dir/verify-report.md" "$dest_dir/verify-report.md"
  copy_file_if_exists "$src_dir/review-report.md" "$dest_dir/review-report.md"
  write_bridge_meta "$dest_dir" "$stage"

  echo "[OK] exported change: $CHANGE_ID"
  echo "[INFO] from=$src_dir"
  echo "[INFO] to=$dest_dir"
  echo "[INFO] gdk_stage=$stage"
}

print_status_map() {
  cat <<'MAP'
OpenSpec -> gdk stage mapping
- openspec/changes/archive/*-<change-id> : archived
- openspec/changes/<change-id> + has unchecked tasks (`- [ ]`) : proposed
- openspec/changes/<change-id> + all tasks checked : applied

gdk -> OpenSpec export mapping
- no --archive-date: export to openspec/changes/<change-id>
- with --archive-date YYYY-MM-DD: export to openspec/changes/archive/YYYY-MM-DD-<change-id>
MAP
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

ACTION="$1"
shift

CHANGE_ID=""
OPENSPEC_ROOT="${PWD}/openspec"
GDK_ROOT="$ROOT_DIR/docs/changes"
FROM_ARCHIVE=0
ARCHIVE_DATE=""
STAGE_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --change)
      CHANGE_ID="$2"
      shift 2
      ;;
    --openspec-root)
      OPENSPEC_ROOT="$2"
      shift 2
      ;;
    --gdk-root)
      GDK_ROOT="$2"
      shift 2
      ;;
    --from-archive)
      FROM_ARCHIVE=1
      shift
      ;;
    --archive-date)
      ARCHIVE_DATE="$2"
      shift 2
      ;;
    --stage)
      STAGE_OVERRIDE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

case "$ACTION" in
  import)
    [[ -d "$OPENSPEC_ROOT" ]] || fail "openspec root not found: $OPENSPEC_ROOT"
    [[ -d "$GDK_ROOT" ]] || fail "gdk change root not found: $GDK_ROOT"
    ensure_kebab_change_id "$CHANGE_ID"
    if [[ -n "$ARCHIVE_DATE" ]]; then
      fail "--archive-date only supports export action"
    fi
    if [[ -n "$STAGE_OVERRIDE" ]]; then
      ensure_stage_value "$STAGE_OVERRIDE"
    fi
    import_change
    ;;
  export)
    [[ -d "$OPENSPEC_ROOT" ]] || fail "openspec root not found: $OPENSPEC_ROOT"
    [[ -d "$GDK_ROOT" ]] || fail "gdk change root not found: $GDK_ROOT"
    ensure_kebab_change_id "$CHANGE_ID"
    if [[ "$FROM_ARCHIVE" -eq 1 ]]; then
      fail "--from-archive only supports import action"
    fi
    if [[ -n "$STAGE_OVERRIDE" ]]; then
      fail "--stage only supports import action"
    fi
    export_change
    ;;
  status-map)
    print_status_map
    ;;
  *)
    fail "unknown action: $ACTION"
    ;;
esac
