#!/usr/bin/env bash
set -euo pipefail
# 加载公共日志库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib-logging.sh"

# ============================================================================
# health-check.sh — agent-dev-kit 仓库内健康检查
#
# 职责: 检查 agent-dev-kit 仓库内部的健康状态
# 特点: 功能更专注，仅检查仓库内部内容
# 对应: llm_agent/scripts/health-check.sh 是工作区级完整版
# ============================================================================
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
    cat <<USAGE
健康检查脚本

Usage:
  ./scripts/health-check.sh <command> [options]

Commands:
  check-all              执行所有健康检查
  check-structure        检查目录结构
  check-dependencies     检查依赖
  check-configuration    检查配置
  check-tests            检查测试
  check-quality          检查质量

Options:
  --verbose              详细输出
  --fix                  自动修复问题
  -h, --help             显示帮助

Examples:
  ./scripts/health-check.sh check-all
  ./scripts/health-check.sh check-structure --verbose
USAGE
}

check_structure() {
    local verbose="$1"
    log_info "检查目录结构..."
    local errors=()
    
    local required_dirs=("agents" "skills" "optional-skills" "scripts" "tests" "docs" "templates")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$ROOT_DIR/$dir" ]]; then
            errors+=("缺失目录: $dir")
        elif [[ "$verbose" == "true" ]]; then
            log_info "目录存在: $dir"
        fi
    done
    
    local required_files=("manifest.yaml" "README.md" "CONTEXT.md")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$ROOT_DIR/$file" ]]; then
            errors+=("缺失文件: $file")
        elif [[ "$verbose" == "true" ]]; then
            log_info "文件存在: $file"
        fi
    done
    
    if [[ ${#errors[@]} -eq 0 ]]; then
        log_success "目录结构检查通过"
        return 0
    else
        log_error "目录结构检查失败:"
        for error in "${errors[@]}"; do echo "  - $error"; done
        return 1
    fi
}

check_dependencies() {
    local verbose="$1"
    log_info "检查依赖..."
    local errors=()
    
    if ! command -v bash &> /dev/null; then
        errors+=("未安装Bash")
    elif [[ "$verbose" == "true" ]]; then
        log_info "Bash已安装: $(bash --version | head -1)"
    fi
    
    if ! command -v git &> /dev/null; then
        errors+=("未安装Git")
    elif [[ "$verbose" == "true" ]]; then
        log_info "Git已安装: $(git --version)"
    fi
    
    local tools=("tar" "grep" "sed" "awk" "rg")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            errors+=("未安装$tool")
        elif [[ "$verbose" == "true" ]]; then
            log_info "$tool已安装"
        fi
    done
    
    if [[ ${#errors[@]} -eq 0 ]]; then
        log_success "依赖检查通过"
        return 0
    else
        log_error "依赖检查失败:"
        for error in "${errors[@]}"; do echo "  - $error"; done
        return 1
    fi
}

check_configuration() {
    local verbose="$1"
    log_info "检查配置..."
    local errors=()
    
    if [[ ! -f "$ROOT_DIR/manifest.yaml" ]]; then
        errors+=("缺失manifest.yaml")
    else
        local required_fields=("version" "profiles" "agents" "skills")
        for field in "${required_fields[@]}"; do
            if ! grep -q "^$field:" "$ROOT_DIR/manifest.yaml"; then
                errors+=("manifest.yaml缺少$field字段")
            elif [[ "$verbose" == "true" ]]; then
                log_info "manifest.yaml包含$field字段"
            fi
        done
    fi
    
    if [[ ! -f "$ROOT_DIR/CONTEXT.md" ]]; then
        errors+=("缺失CONTEXT.md")
    elif [[ "$verbose" == "true" ]]; then
        log_info "CONTEXT.md存在"
    fi
    
    if [[ ${#errors[@]} -eq 0 ]]; then
        log_success "配置检查通过"
        return 0
    else
        log_error "配置检查失败:"
        for error in "${errors[@]}"; do echo "  - $error"; done
        return 1
    fi
}

check_tests() {
    local verbose="$1"
    local fix="$2"
    log_info "检查测试..."
    local errors=()
    
    if [[ ! -d "$ROOT_DIR/tests" ]]; then
        errors+=("缺失tests目录")
    else
        local test_count
        test_count=$(find "$ROOT_DIR/tests" -name "test_*.sh" -type f | wc -l)
        if [[ "$test_count" -eq 0 ]]; then
            errors+=("没有测试文件")
        elif [[ "$verbose" == "true" ]]; then
            log_info "发现 $test_count 个测试文件"
        fi
    fi
    
    if [[ "$fix" == "true" ]]; then
        log_info "运行测试..."
        if bash "$ROOT_DIR/tests/run_all.sh" >/dev/null 2>&1; then
            log_success "测试通过"
        else
            errors+=("测试失败")
        fi
    fi
    
    if [[ ${#errors[@]} -eq 0 ]]; then
        log_success "测试检查通过"
        return 0
    else
        log_error "测试检查失败:"
        for error in "${errors[@]}"; do echo "  - $error"; done
        return 1
    fi
}

check_quality() {
    local verbose="$1"
    log_info "检查质量..."
    local errors=()
    
    if [[ -f "$ROOT_DIR/scripts/quality-gate-check.sh" ]]; then
        if ! bash "$ROOT_DIR/scripts/quality-gate-check.sh" check-all >/dev/null 2>&1; then
            errors+=("质量门禁检查失败")
        elif [[ "$verbose" == "true" ]]; then
            log_info "质量门禁检查通过"
        fi
    else
        errors+=("缺失quality-gate-check.sh脚本")
    fi
    
    if [[ ${#errors[@]} -eq 0 ]]; then
        log_success "质量检查通过"
        return 0
    else
        log_error "质量检查失败:"
        for error in "${errors[@]}"; do echo "  - $error"; done
        return 1
    fi
}

check_all() {
    local verbose="$1"
    local fix="$2"
    log_info "执行所有健康检查..."
    local all_passed=true
    
    if ! check_structure "$verbose"; then all_passed=false; fi
    if ! check_dependencies "$verbose"; then all_passed=false; fi
    if ! check_configuration "$verbose"; then all_passed=false; fi
    if ! check_tests "$verbose" "$fix"; then all_passed=false; fi
    if ! check_quality "$verbose"; then all_passed=false; fi
    
    if [[ "$all_passed" == "true" ]]; then
        log_success "所有健康检查通过"
        return 0
    else
        log_error "健康检查失败"
        return 1
    fi
}

main() {
    if [[ $# -lt 1 ]]; then usage; exit 1; fi
    
    local command="$1"; shift
    local verbose="false"
    local fix="false"
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --verbose) verbose="true"; shift ;;
            --fix) fix="true"; shift ;;
            -h|--help) usage; exit 0 ;;
            *) log_error "未知参数: $1"; usage; exit 1 ;;
        esac
    done
    
    case "$command" in
        check-all) check_all "$verbose" "$fix" ;;
        check-structure) check_structure "$verbose" ;;
        check-dependencies) check_dependencies "$verbose" ;;
        check-configuration) check_configuration "$verbose" ;;
        check-tests) check_tests "$verbose" "$fix" ;;
        check-quality) check_quality "$verbose" ;;
        *) log_error "未知命令: $command"; usage; exit 1 ;;
    esac
}

main "$@"
