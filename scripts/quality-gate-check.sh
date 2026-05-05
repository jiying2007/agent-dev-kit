#!/usr/bin/env bash
set -euo pipefail

# 质量门禁检查脚本
# 检查Artifact/Gate协议的完整性

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 使用说明
usage() {
    cat <<USAGE
质量门禁检查脚本

Usage:
  ./scripts/quality-gate-check.sh <command> [options]

Commands:
  check-all              检查所有质量门禁
  check-artifacts        检查产物完整性
  check-consistency      检查一致性
  check-evidence         检查验证证据
  check-profiles         检查Profile配置

Options:
  --strict               严格模式
  --verbose              详细输出
  -h, --help             显示帮助

Examples:
  ./scripts/quality-gate-check.sh check-all --strict
  ./scripts/quality-gate-check.sh check-artifacts --verbose
USAGE
}

# 检查产物完整性
check_artifacts() {
    local strict="$1"
    local verbose="$2"
    
    log_info "检查产物完整性..."
    
    local errors=()
    
    # 检查模板文件
    local templates=(
        "templates/artifacts/prd-template.md"
        "templates/artifacts/user-story-template.md"
        "templates/artifacts/design-spec-template.md"
        "templates/artifacts/system-arch-template.md"
        "templates/artifacts/task-breakdown-template.md"
        "templates/artifacts/implementation-plan-template.md"
        "templates/artifacts/review-report-template.md"
        "templates/artifacts/test-report-template.md"
        "templates/artifacts/approval-template.md"
    )
    
    for template in "${templates[@]}"; do
        if [[ ! -f "$ROOT_DIR/$template" ]]; then
            errors+=("缺失模板: $template")
        elif [[ "$verbose" == "true" ]]; then
            log_info "检查模板: $template"
            
            # 检查artifact标签
            if ! grep -q "\[artifact:" "$ROOT_DIR/$template"; then
                errors+=("模板缺少artifact标签: $template")
            fi
            
            # 检查status字段
            if ! grep -q "status:" "$ROOT_DIR/$template"; then
                errors+=("模板缺少status字段: $template")
            fi
            
            # 检查owner字段
            if ! grep -q "owner:" "$ROOT_DIR/$template"; then
                errors+=("模板缺少owner字段: $template")
            fi
        fi
    done
    
    # 检查工作流模板
    local workflows=(
        "templates/workflows/standard-workflow-template.md"
        "templates/workflows/emergency-workflow-template.md"
    )
    
    for workflow in "${workflows[@]}"; do
        if [[ ! -f "$ROOT_DIR/$workflow" ]]; then
            errors+=("缺失工作流模板: $workflow")
        fi
    done
    
    # 输出结果
    if [[ ${#errors[@]} -eq 0 ]]; then
        log_success "产物完整性检查通过"
        return 0
    else
        log_error "产物完整性检查失败:"
        for error in "${errors[@]}"; do
            echo "  - $error"
        done
        return 1
    fi
}

# 检查一致性
check_consistency() {
    local strict="$1"
    local verbose="$2"
    
    log_info "检查一致性..."
    
    local errors=()
    
    # 检查CONTEXT.md
    if [[ ! -f "$ROOT_DIR/CONTEXT.md" ]]; then
        errors+=("缺失CONTEXT.md")
    else
        # 检查核心概念
        local concepts=("Agent" "Skill" "Profile" "Workflow" "Artifact" "Gate")
        for concept in "${concepts[@]}"; do
            if ! grep -q "$concept" "$ROOT_DIR/CONTEXT.md"; then
                errors+=("CONTEXT.md缺少核心概念: $concept")
            fi
        done
    fi
    
    # 检查文档目录
    local docs=(
        "docs/changes/README.md"
        "docs/specs/README.md"
        "docs/explorations/README.md"
        "docs/skill-composition-guide.md"
    )
    
    for doc in "${docs[@]}"; do
        if [[ ! -f "$ROOT_DIR/$doc" ]]; then
            errors+=("缺失文档: $doc")
        fi
    done
    
    # 检查Profile配置
    if [[ -f "$ROOT_DIR/manifest.yaml" ]]; then
        # 检查Profile继承关系
        local profiles
        profiles=$(grep -A 1 "^  [a-z].*:" "$ROOT_DIR/manifest.yaml" | grep "extends:" | wc -l)
        if [[ "$verbose" == "true" ]]; then
            log_info "发现 $profiles 个Profile继承关系"
        fi
    fi
    
    # 输出结果
    if [[ ${#errors[@]} -eq 0 ]]; then
        log_success "一致性检查通过"
        return 0
    else
        log_error "一致性检查失败:"
        for error in "${errors[@]}"; do
            echo "  - $error"
        done
        return 1
    fi
}

# 检查验证证据
check_evidence() {
    local strict="$1"
    local verbose="$2"
    
    log_info "检查验证证据..."
    
    local errors=()
    
    # 检查测试文件
    local tests=(
        "tests/test_enhanced_gate_check.sh"
        "tests/test_templates.sh"
        "tests/test_context_md.sh"
        "tests/test_boundary_conditions.sh"
        "tests/test_integration.sh"
    )
    
    for test in "${tests[@]}"; do
        if [[ ! -f "$ROOT_DIR/$test" ]]; then
            errors+=("缺失测试文件: $test")
        elif [[ ! -x "$ROOT_DIR/$test" ]]; then
            errors+=("测试文件不可执行: $test")
        fi
    done
    
    # 检查脚本文件
    local scripts=(
    )
    
    for script in "${scripts[@]}"; do
        if [[ ! -f "$ROOT_DIR/$script" ]]; then
            errors+=("缺失脚本文件: $script")
        elif [[ ! -x "$ROOT_DIR/$script" ]]; then
            errors+=("脚本文件不可执行: $script")
        fi
    done
    
    # 输出结果
    if [[ ${#errors[@]} -eq 0 ]]; then
        log_success "验证证据检查通过"
        return 0
    else
        log_error "验证证据检查失败:"
        for error in "${errors[@]}"; do
            echo "  - $error"
        done
        return 1
    fi
}

# 检查Profile配置
check_profiles() {
    local strict="$1"
    local verbose="$2"
    
    log_info "检查Profile配置..."
    
    local errors=()
    
    # 检查manifest.yaml
    if [[ ! -f "$ROOT_DIR/manifest.yaml" ]]; then
        errors+=("缺失manifest.yaml")
    else
        # 检查Profile定义
        local profiles
        profiles=$(grep -E "^  [a-z].*:" "$ROOT_DIR/manifest.yaml" | grep -v "extends:" | wc -l)
        if [[ "$verbose" == "true" ]]; then
            log_info "发现 $profiles 个Profile定义"
        fi
        
        # 检查默认Profile
        if ! grep -q "default_profile:" "$ROOT_DIR/manifest.yaml"; then
            errors+=("manifest.yaml缺少default_profile定义")
        fi
        
        # 检查Profile继承循环
        local profile_names
        profile_names=$(grep -E "^  [a-z].*:" "$ROOT_DIR/manifest.yaml" | grep -v "extends:" | sed 's/://g' | tr -d ' ')
        
        for profile in $profile_names; do
            local extends
            extends=$(grep -A 5 "^  $profile:" "$ROOT_DIR/manifest.yaml" | grep "extends:" | head -1 | awk '{print $2}' || true)
            
            if [[ -n "$extends" ]]; then
                # 检查继承的Profile是否存在
                if ! echo "$profile_names" | grep -q "^$extends$"; then
                    errors+=("Profile $profile 继承的 $extends 不存在")
                fi
            fi
        done
    fi
    
    # 输出结果
    if [[ ${#errors[@]} -eq 0 ]]; then
        log_success "Profile配置检查通过"
        return 0
    else
        log_error "Profile配置检查失败:"
        for error in "${errors[@]}"; do
            echo "  - $error"
        done
        return 1
    fi
}

# 检查所有质量门禁
check_all() {
    local strict="$1"
    local verbose="$2"
    
    log_info "检查所有质量门禁..."
    
    local all_passed=true
    
    if ! check_artifacts "$strict" "$verbose"; then
        all_passed=false
    fi
    
    if ! check_consistency "$strict" "$verbose"; then
        all_passed=false
    fi
    
    if ! check_evidence "$strict" "$verbose"; then
        all_passed=false
    fi
    
    if ! check_profiles "$strict" "$verbose"; then
        all_passed=false
    fi
    
    if [[ "$all_passed" == "true" ]]; then
        log_success "所有质量门禁检查通过"
        return 0
    else
        log_error "质量门禁检查失败"
        return 1
    fi
}

# 主函数
main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi
    
    local command="$1"
    shift
    
    local strict="false"
    local verbose="false"
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --strict)
                strict="true"
                shift
                ;;
            --verbose)
                verbose="true"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    case "$command" in
        check-all)
            check_all "$strict" "$verbose"
            ;;
        check-artifacts)
            check_artifacts "$strict" "$verbose"
            ;;
        check-consistency)
            check_consistency "$strict" "$verbose"
            ;;
        check-evidence)
            check_evidence "$strict" "$verbose"
            ;;
        check-profiles)
            check_profiles "$strict" "$verbose"
            ;;
        *)
            log_error "未知命令: $command"
            usage
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"