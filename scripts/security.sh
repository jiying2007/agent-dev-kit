#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
    cat <<USAGE
安全加固脚本

Usage:
  ./scripts/security.sh <command> [options]

Commands:
  scan                   安全扫描
  harden                 安全加固
  audit                  安全审计
  report                 生成报告

Options:
  --level <level>        安全级别
  --fix                  自动修复
  -h, --help             显示帮助

Examples:
  ./scripts/security.sh scan
  ./scripts/security.sh harden --level basic
  ./scripts/security.sh audit
USAGE
}

security_scan() {
    log_info "安全扫描"
    
    local issues=()
    
    # 1. 文件权限检查
    log_info "1. 文件权限检查"
    local world_writable=$(find "$ROOT_DIR" -type f -perm -o+w 2>/dev/null | wc -l)
    if [[ "$world_writable" -gt 0 ]]; then
        issues+=("发现 $world_writable 个世界可写文件")
    fi
    
    # 2. 敏感文件检查
    log_info "2. 敏感文件检查"
    local sensitive_patterns=(".env" "*.key" "*.pem" "*.p12" "*.pfx" "*.jks")
    for pattern in "${sensitive_patterns[@]}"; do
        local found=$(find "$ROOT_DIR" -name "$pattern" -type f 2>/dev/null | wc -l)
        if [[ "$found" -gt 0 ]]; then
            issues+=("发现 $found 个敏感文件: $pattern")
        fi
    done
    
    # 3. 脚本安全检查
    log_info "3. 脚本安全检查"
    local scripts_with_sudo=$(grep -r "sudo" "$ROOT_DIR/scripts" 2>/dev/null | wc -l)
    if [[ "$scripts_with_sudo" -gt 0 ]]; then
        issues+=("发现 $scripts_with_sudo 个脚本使用sudo")
    fi
    
    local scripts_with_eval=$(grep -r "eval" "$ROOT_DIR/scripts" 2>/dev/null | wc -l)
    if [[ "$scripts_with_eval" -gt 0 ]]; then
        issues+=("发现 $scripts_with_eval 个脚本使用eval")
    fi
    
    # 4. 配置文件检查
    log_info "4. 配置文件检查"
    local config_files=(".gitconfig" ".ssh" ".gnupg")
    for config in "${config_files[@]}"; do
        if [[ -e "$ROOT_DIR/$config" ]]; then
            issues+=("发现配置文件: $config")
        fi
    done
    
    # 5. 网络服务检查
    log_info "5. 网络服务检查"
    local open_ports=$(netstat -tuln 2>/dev/null | grep -c "LISTEN" || echo "0")
    if [[ "$open_ports" -gt 0 ]]; then
        issues+=("发现 $open_ports 个开放端口")
    fi
    
    if [[ ${#issues[@]} -eq 0 ]]; then
        log_success "安全扫描通过"
    else
        log_warning "安全扫描发现问题:"
        for issue in "${issues[@]}"; do echo "  - $issue"; done
    fi
}

security_harden() {
    local level="$1" fix="$2"
    log_info "安全加固 (级别: $level)"
    
    case "$level" in
        basic)
            log_info "基础加固"
            # 修复文件权限
            if [[ "$fix" == "true" ]]; then
                find "$ROOT_DIR" -type f -perm -o+w -exec chmod o-w {} \; 2>/dev/null || true
                find "$ROOT_DIR/scripts" -name "*.sh" -type f -exec chmod 755 {} \; 2>/dev/null || true
                find "$ROOT_DIR/tests" -name "*.sh" -type f -exec chmod 755 {} \; 2>/dev/null || true
            fi
            ;;
        medium)
            log_info "中等加固"
            # 基础加固
            security_harden "basic" "$fix"
            # 设置目录权限
            if [[ "$fix" == "true" ]]; then
                chmod 755 "$ROOT_DIR/scripts" 2>/dev/null || true
                chmod 755 "$ROOT_DIR/tests" 2>/dev/null || true
                chmod 755 "$ROOT_DIR/docs" 2>/dev/null || true
            fi
            ;;
        advanced)
            log_info "高级加固"
            # 中等加固
            security_harden "medium" "$fix"
            # 创建安全配置
            if [[ "$fix" == "true" ]]; then
                cat > "$ROOT_DIR/.security-config" <<EOF
# 安全配置
# 生成时间: $(date)

# 文件权限
UMASK=022

# 目录权限
DIR_PERMS=755
FILE_PERMS=644
SCRIPT_PERMS=755

# 安全策略
ALLOW_WORLD_WRITABLE=false
ALLOW_SENSITIVE_FILES=false
ALLOW_SUDO=false
ALLOW_EVAL=false
EOF
            fi
            ;;
    esac
    
    log_success "安全加固完成"
}

security_audit() {
    log_info "安全审计"
    
    echo "=== 安全审计报告 ==="
    echo ""
    
    # 1. 系统信息
    echo "1. 系统信息:"
    echo "   - 操作系统: $(uname -s)"
    echo "   - 内核版本: $(uname -r)"
    echo "   - 架构: $(uname -m)"
    echo ""
    
    # 2. 用户信息
    echo "2. 用户信息:"
    echo "   - 当前用户: $(whoami)"
    echo "   - 用户ID: $(id -u)"
    echo "   - 组ID: $(id -g)"
    echo ""
    
    # 3. 文件权限
    echo "3. 文件权限:"
    echo "   - 世界可写文件: $(find "$ROOT_DIR" -type f -perm -o+w 2>/dev/null | wc -l)"
    echo "   - 可执行文件: $(find "$ROOT_DIR" -type f -executable 2>/dev/null | wc -l)"
    echo ""
    
    # 4. 敏感文件
    echo "4. 敏感文件:"
    local sensitive_patterns=(".env" "*.key" "*.pem" "*.p12" "*.pfx" "*.jks")
    for pattern in "${sensitive_patterns[@]}"; do
        local found=$(find "$ROOT_DIR" -name "$pattern" -type f 2>/dev/null | wc -l)
        echo "   - $pattern: $found"
    done
    echo ""
    
    # 5. 脚本安全
    echo "5. 脚本安全:"
    echo "   - 使用sudo的脚本: $(grep -r "sudo" "$ROOT_DIR/scripts" 2>/dev/null | wc -l)"
    echo "   - 使用eval的脚本: $(grep -r "eval" "$ROOT_DIR/scripts" 2>/dev/null | wc -l)"
    echo "   - 使用curl的脚本: $(grep -r "curl" "$ROOT_DIR/scripts" 2>/dev/null | wc -l)"
    echo ""
    
    # 6. 网络服务
    echo "6. 网络服务:"
    echo "   - 开放端口: $(netstat -tuln 2>/dev/null | grep -c "LISTEN" || echo "0")"
    echo ""
    
    # 7. 安全建议
    echo "7. 安全建议:"
    echo "   - 定期运行安全扫描"
    echo "   - 及时修复安全问题"
    echo "   - 监控敏感文件"
    echo "   - 限制脚本权限"
}

generate_report() {
    log_info "生成安全报告"
    
    local report_file="$ROOT_DIR/.monitoring/security-report-$(date +%Y%m%d%H%M%S).md"
    
    cat > "$report_file" <<EOF
# 安全报告

## 报告信息
- 生成时间: $(date)
- 系统信息: $(uname -a)

## 系统信息
- 操作系统: $(uname -s)
- 内核版本: $(uname -r)
- 架构: $(uname -m)
- 当前用户: $(whoami)
- 用户ID: $(id -u)
- 组ID: $(id -g)

## 文件权限
- 世界可写文件: $(find "$ROOT_DIR" -type f -perm -o+w 2>/dev/null | wc -l)
- 可执行文件: $(find "$ROOT_DIR" -type f -executable 2>/dev/null | wc -l)

## 敏感文件
$(for pattern in ".env" "*.key" "*.pem" "*.p12" "*.pfx" "*.jks"; do
    echo "- $pattern: $(find "$ROOT_DIR" -name "$pattern" -type f 2>/dev/null | wc -l)"
done)

## 脚本安全
- 使用sudo的脚本: $(grep -r "sudo" "$ROOT_DIR/scripts" 2>/dev/null | wc -l)
- 使用eval的脚本: $(grep -r "eval" "$ROOT_DIR/scripts" 2>/dev/null | wc -l)
- 使用curl的脚本: $(grep -r "curl" "$ROOT_DIR/scripts" 2>/dev/null | wc -l)

## 网络服务
- 开放端口: $(netstat -tuln 2>/dev/null | grep -c "LISTEN" || echo "0")

## 安全建议
1. 定期运行安全扫描
2. 及时修复安全问题
3. 监控敏感文件
4. 限制脚本权限
5. 使用安全配置
6. 定期审计日志
EOF
    
    log_success "安全报告已生成: $report_file"
}

main() {
    [[ $# -lt 1 ]] && { usage; exit 1; }
    local command="$1"; shift
    local level="basic" fix="false"
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --level) level="$2"; shift 2 ;;
            --fix) fix="true"; shift ;;
            -h|--help) usage; exit 0 ;;
            *) log_error "未知参数: $1"; usage; exit 1 ;;
        esac
    done
    
    case "$command" in
        scan) security_scan ;;
        harden) security_harden "$level" "$fix" ;;
        audit) security_audit ;;
        report) generate_report ;;
        *) log_error "未知命令: $command"; usage; exit 1 ;;
    esac
}

main "$@"
