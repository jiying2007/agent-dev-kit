#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
  cat <<'USAGE'
质量门禁检查脚本

Usage:
  ./scripts/quality-gate-check.sh <command> [options]

Commands:
  check-all              检查所有质量门禁
  check-artifacts        检查产物完整性
  check-consistency      检查领域上下文与文档一致性
  check-evidence         检查验证证据入口
  check-profiles         检查 Profile typed contract

Options:
  --strict               严格模式
  --verbose              详细输出
  -h, --help             显示帮助
USAGE
}

check_artifacts() {
  local verbose="$1"
  local errors=0 path
  log_info "检查产物完整性..."
  local templates=(
    templates/artifacts/prd-template.md
    templates/artifacts/user-story-template.md
    templates/artifacts/design-spec-template.md
    templates/artifacts/system-arch-template.md
    templates/artifacts/task-breakdown-template.md
    templates/artifacts/implementation-plan-template.md
    templates/artifacts/target-architecture-report-template.md
    templates/artifacts/review-report-template.md
    templates/artifacts/test-report-template.md
    templates/artifacts/approval-template.md
    templates/workflows/standard-workflow-template.md
    templates/workflows/emergency-workflow-template.md
  )
  for path in "${templates[@]}"; do
    if [[ ! -f "$ROOT_DIR/$path" ]]; then
      log_error "缺失产物模板: $path"
      errors=1
    elif [[ "$verbose" == true ]]; then
      log_info "已验证: $path"
    fi
  done
  [[ "$errors" -eq 0 ]] || return 1
  log_success "产物完整性检查通过"
}

check_consistency() {
  local verbose="$1"
  log_info "检查一致性..."
  bash "$ROOT_DIR/tests/test_context_md.sh" >/dev/null || {
    log_error "CONTEXT/Manifest 语义合同失败"
    return 1
  }
  local doc
  for doc in docs/changes/README.md docs/specs/README.md docs/explorations/README.md docs/skill-composition-guide.md; do
    [[ -f "$ROOT_DIR/$doc" ]] || {
      log_error "缺失文档: $doc"
      return 1
    }
  done
  if [[ "$verbose" == true ]]; then
    log_info "Manifest canonical source: manifest.json"
  fi
  log_success "一致性检查通过"
}

check_evidence() {
  local verbose="$1"
  log_info "检查验证证据..."
  local test
  for test in \
    tests/test_enhanced_gate_check.sh \
    tests/test_templates.sh \
    tests/test_context_md.sh \
    tests/test_boundary_conditions.sh \
    tests/test_integration.sh; do
    [[ -f "$ROOT_DIR/$test" && -x "$ROOT_DIR/$test" ]] || {
      log_error "验证入口缺失或不可执行: $test"
      return 1
    }
    [[ "$verbose" == true ]] && log_info "已验证: $test"
  done
  log_success "验证证据检查通过"
}

check_profiles() {
  local verbose="$1"
  log_info "检查Profile配置..."
  local output
  if ! output="$(bash "$ROOT_DIR/scripts/check-profile-coherence.sh" 2>&1)"; then
    printf '%s\n' "$output" >&2
    log_error "Profile typed contract 失败"
    return 1
  fi
  [[ "$verbose" == true ]] && printf '%s\n' "$output"
  log_success "Profile配置检查通过"
}

check_all() {
  local verbose="$1"
  log_info "检查所有质量门禁..."
  local failed=0
  check_artifacts "$verbose" || failed=1
  check_consistency "$verbose" || failed=1
  check_evidence "$verbose" || failed=1
  check_profiles "$verbose" || failed=1
  if [[ "$failed" -eq 0 ]]; then
    log_success "所有质量门禁检查通过"
    return 0
  fi
  log_error "质量门禁检查失败"
  return 1
}

main() {
  [[ $# -ge 1 ]] || { usage; exit 1; }
  local command="$1"
  shift
  local strict=false verbose=false
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --strict) strict=true; shift ;;
      --verbose) verbose=true; shift ;;
      -h|--help) usage; exit 0 ;;
      *) log_error "未知参数: $1"; usage; exit 1 ;;
    esac
  done
  # --strict remains an accepted compatibility flag, but strictness is delegated
  # to the typed contracts instead of selecting a second implementation.
  [[ "$strict" == true && "$verbose" == true ]] && log_info "strict typed contracts enabled"
  case "$command" in
    check-all) check_all "$verbose" ;;
    check-artifacts) check_artifacts "$verbose" ;;
    check-consistency) check_consistency "$verbose" ;;
    check-evidence) check_evidence "$verbose" ;;
    check-profiles) check_profiles "$verbose" ;;
    *) log_error "未知命令: $command"; usage; exit 1 ;;
  esac
}

main "$@"
