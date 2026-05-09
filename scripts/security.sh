#!/usr/bin/env bash
set -euo pipefail

# 加载公共日志库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib-logging.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

; ; ; BLUE='\033[0;34m'; 
[INFO]${NC} $1"; }
[SUCCESS]${NC} $1"; }
[WARNING]${NC} $1"; }
[ERROR]${NC} $1"; }

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
