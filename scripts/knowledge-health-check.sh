#!/usr/bin/env bash
# knowledge-health-check.sh — 知识健康检查脚本
# 来源: 腾讯技术工程文章《Harness不是目的，知识才是护城河》
# 实施日期: 2026-05-12

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KNOWLEDGE_DIR="$PROJECT_ROOT/knowledge"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }

usage() {
    cat <<EOF
知识健康检查工具

用法: $(basename "$0") <command> [options]

命令:
  check-all          运行所有检查
  check-structure    检查目录结构完整性
  check-maturity     检查成熟度标记
  check-references   检查引用完整性
  check-staleness    检查过期知识
  check-coverage     检查知识覆盖度
  stats              显示知识统计

选项:
  --fix              自动修复可修复的问题
  --verbose          显示详细信息
  -h, --help         显示帮助

示例:
  $(basename "$0") check-all
  $(basename "$0") check-staleness --verbose
  $(basename "$0") stats
EOF
}

# 检查目录结构完整性
check_structure() {
    log_info "检查知识目录结构..."
    local pass=0
    local fail=0
    
    # 检查五层目录
    for layer in L0-toolchain L1-general-tech L2-domain L3-project L4-session; do
        if [[ -d "$KNOWLEDGE_DIR/$layer" ]]; then
            log_success "目录存在: $layer"
            ((pass++))
        else
            log_error "目录缺失: $layer"
            ((fail++))
        fi
    done
    
    # 检查必需文件
    for file in README.md INDEX.md; do
        if [[ -f "$KNOWLEDGE_DIR/$file" ]]; then
            log_success "文件存在: $file"
            ((pass++))
        else
            log_error "文件缺失: $file"
            ((fail++))
        fi
    done
    
    echo ""
    log_info "结构检查: $pass 通过, $fail 失败"
    return $fail
}

# 检查成熟度标记
check_maturity() {
    log_info "检查知识成熟度标记..."
    local pass=0
    local fail=0
    local warn=0
    
    while IFS= read -r file; do
        if grep -q "maturity:" "$file" || grep -q "成熟度:" "$file"; then
            local maturity
            maturity=$(grep -E "(maturity:|成熟度:)" "$file" | head -1 | sed 's/.*[:：] *//')
            case "$maturity" in
                draft|verified|mature)
                    log_success "成熟度有效: $(basename "$file") = $maturity"
                    ((pass++))
                    ;;
                *)
                    log_error "成熟度无效: $(basename "$file") = $maturity"
                    ((fail++))
                    ;;
            esac
        else
            log_warning "缺少成熟度标记: $(basename "$file")"
            ((warn++))
        fi
    done < <(find "$KNOWLEDGE_DIR" -name "*.md" -not -name "README.md" -not -name "INDEX.md")
    
    echo ""
    log_info "成熟度检查: $pass 通过, $fail 失败, $warn 警告"
    return $fail
}

# 检查引用完整性
check_references() {
    log_info "检查知识引用完整性..."
    local pass=0
    local fail=0
    
    # 检查知识文件之间的引用
    while IFS= read -r file; do
        # 提取文件中引用的其他 .md 文件
        while IFS= read -r ref; do
            if [[ -n "$ref" && "$ref" != *.md ]]; then
                continue
            fi
            # 跳过 README.md 和 INDEX.md
            if [[ "$ref" == "README.md" || "$ref" == "INDEX.md" ]]; then
                continue
            fi
            # 检查引用的文件是否存在
            if [[ -n "$ref" ]]; then
                local found
                found=$(find "$KNOWLEDGE_DIR" -name "$ref" 2>/dev/null | head -1)
                if [[ -n "$found" ]]; then
                    ((pass++))
                else
                    # 检查是否是 docs/ 引用（合法）
                    if grep -q "docs/" "$file" && grep -q "$ref" "$file"; then
                        ((pass++))  # docs/ 引用是合法的
                    else
                        log_warning "引用可能断裂: $(basename "$file") -> $ref"
                        ((fail++))
                    fi
                fi
            fi
        done < <(grep -oP '[a-zA-Z0-9_-]+\.md' "$file" 2>/dev/null | sort -u)
    done < <(find "$KNOWLEDGE_DIR" -name "*.md" -not -name "README.md" -not -name "INDEX.md")
    
    echo ""
    log_info "引用检查: $pass 通过, $fail 失败"
    return $fail
}

# 检查过期知识
check_staleness() {
    log_info "检查过期知识..."
    local stale_count=0
    local total=0
    
    while IFS= read -r file; do
        ((total++))
        # 检查最后修改时间
        local days_since_modified
        days_since_modified=$(( ($(date +%s) - $(stat -c %Y "$file")) / 86400 ))
        
        if [[ $days_since_modified -gt 180 ]]; then
            log_warning "过期知识 ($days_since_modified 天): $(basename "$file")"
            ((stale_count++))
        fi
    done < <(find "$KNOWLEDGE_DIR" -name "*.md" -not -name "README.md" -not -name "INDEX.md")
    
    echo ""
    log_info "过期检查: $stale_count/$total 个知识过期 (>180天)"
    return 0
}

# 检查知识覆盖度
check_coverage() {
    log_info "检查知识覆盖度..."
    
    # 统计各层级
    echo ""
    echo "=== 按层级统计 ==="
    for layer in L0-toolchain L1-general-tech L2-domain L3-project L4-session; do
        local count
        count=$(find "$KNOWLEDGE_DIR/$layer" -name "*.md" 2>/dev/null | wc -l)
        echo "  $layer: $count 个文件"
    done
    
    # 统计成熟度
    echo ""
    echo "=== 按成熟度统计 ==="
    for maturity in draft verified mature; do
        local count
        count=$(grep -r "maturity: $maturity" "$KNOWLEDGE_DIR" 2>/dev/null | wc -l)
        echo "  $maturity: $count 个"
    done
    
    # 统计总文件数
    local total
    total=$(find "$KNOWLEDGE_DIR" -name "*.md" -not -name "README.md" -not -name "INDEX.md" | wc -l)
    echo ""
    log_info "知识总数: $total 个"
    
    return 0
}

# 显示统计信息
stats() {
    echo "=========================================="
    echo "  知识库统计"
    echo "=========================================="
    
    # 总体统计
    local total
    total=$(find "$KNOWLEDGE_DIR" -name "*.md" | wc -l)
    echo ""
    echo "总文件数: $total"
    
    # 按层级统计
    echo ""
    echo "按层级:"
    for layer in L0-toolchain L1-general-tech L2-domain L3-project L4-session; do
        local count
        count=$(find "$KNOWLEDGE_DIR/$layer" -name "*.md" 2>/dev/null | wc -l)
        echo "  $layer: $count"
    done
    
    # 按成熟度统计
    echo ""
    echo "按成熟度:"
    for maturity in draft verified mature; do
        local count
        count=$(grep -r "maturity: $maturity" "$KNOWLEDGE_DIR" 2>/dev/null | wc -l)
        echo "  $maturity: $count"
    done
    
    # 最近更新
    echo ""
    echo "最近更新:"
    find "$KNOWLEDGE_DIR" -name "*.md" -not -name "README.md" -not -name "INDEX.md" -printf "%T@ %p\n" | sort -rn | head -5 | while read -r ts file; do
        echo "  $(date -d "@$ts" "+%Y-%m-%d") $(basename "$file")"
    done
    
    echo ""
    echo "=========================================="
}

# 主函数
main() {
    local command="${1:-help}"
    shift || true
    
    case "$command" in
        check-all)
            local total_fail=0
            check_structure || ((total_fail++))
            echo ""
            check_maturity || ((total_fail++))
            echo ""
            check_references || ((total_fail++))
            echo ""
            check_staleness
            echo ""
            check_coverage
            
            echo ""
            echo "=========================================="
            if [[ $total_fail -eq 0 ]]; then
                log_success "所有检查通过"
            else
                log_error "$total_fail 项检查失败"
            fi
            echo "=========================================="
            return $total_fail
            ;;
        check-structure)
            check_structure
            ;;
        check-maturity)
            check_maturity
            ;;
        check-references)
            check_references
            ;;
        check-staleness)
            check_staleness
            ;;
        check-coverage)
            check_coverage
            ;;
        stats)
            stats
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            log_error "未知命令: $command"
            usage
            return 1
            ;;
    esac
}

main "$@"
