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
监控和告警脚本

Usage:
  ./scripts/monitoring.sh <command> [options]

Commands:
  start                  启动监控
  stop                   停止监控
  status                 查看监控状态
  check                  执行检查
  alert                  发送告警
  report                 生成报告

Options:
  --interval <seconds>   检查间隔
  --threshold <value>    告警阈值
  --email <email>        告警邮箱
  --webhook <url>        告警webhook
  -h, --help             显示帮助

Examples:
  ./scripts/monitoring.sh start --interval 60
  ./scripts/monitoring.sh check
  ./scripts/monitoring.sh alert --email admin@example.com
USAGE
}

start_monitoring() {
    local interval="$1"
    log_info "启动监控 (间隔: ${interval}秒)"
    
    # 创建监控目录
    mkdir -p "$ROOT_DIR/.monitoring"
    
    # 创建监控配置
    cat > "$ROOT_DIR/.monitoring/config.json" <<EOF
{
    "interval": $interval,
    "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "pid": $$
}
EOF
    
    # 创建监控日志
    cat > "$ROOT_DIR/.monitoring/monitor.log" <<EOF
监控日志 - 启动时间: $(date)
=====================================
EOF
    
    log_success "监控已启动"
    log_info "监控配置: $ROOT_DIR/.monitoring/config.json"
    log_info "监控日志: $ROOT_DIR/.monitoring/monitor.log"
    
    # 后台监控循环
    while true; do
        check_system
        sleep "$interval"
    done
}

stop_monitoring() {
    log_info "停止监控"
    
    if [[ -f "$ROOT_DIR/.monitoring/config.json" ]]; then
        rm -f "$ROOT_DIR/.monitoring/config.json"
        log_success "监控已停止"
    else
        log_warning "监控未运行"
    fi
}

show_status() {
    log_info "监控状态:"
    
    if [[ -f "$ROOT_DIR/.monitoring/config.json" ]]; then
        echo "状态: 运行中"
        echo "配置: $ROOT_DIR/.monitoring/config.json"
        echo "日志: $ROOT_DIR/.monitoring/monitor.log"
        
        if [[ -f "$ROOT_DIR/.monitoring/monitor.log" ]]; then
            echo ""
            echo "最近日志:"
            tail -10 "$ROOT_DIR/.monitoring/monitor.log"
        fi
    else
        echo "状态: 未运行"
    fi
}

check_system() {
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    # 记录检查
    echo "[$timestamp] 执行系统检查..." >> "$ROOT_DIR/.monitoring/monitor.log"
    
    # 1. 检查磁盘空间
    local disk_usage=$(df -h "$ROOT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ "$disk_usage" -gt 80 ]]; then
        echo "[$timestamp] 告警: 磁盘使用率过高: ${disk_usage}%" >> "$ROOT_DIR/.monitoring/monitor.log"
        send_alert "磁盘使用率过高: ${disk_usage}%"
    fi
    
    # 2. 检查内存使用
    local memory_usage=$(free | awk 'NR==2 {printf "%.0f", $3*100/$2}')
    if [[ "$memory_usage" -gt 80 ]]; then
        echo "[$timestamp] 告警: 内存使用率过高: ${memory_usage}%" >> "$ROOT_DIR/.monitoring/monitor.log"
        send_alert "内存使用率过高: ${memory_usage}%"
    fi
    
    # 3. 检查健康状态
    if ! bash "$ROOT_DIR/scripts/health-check.sh" check-all >/dev/null 2>&1; then
        echo "[$timestamp] 告警: 健康检查失败" >> "$ROOT_DIR/.monitoring/monitor.log"
        send_alert "健康检查失败"
    fi
    
    # 4. 检查测试状态
    if ! bash "$ROOT_DIR/tests/run_all.sh" >/dev/null 2>&1; then
        echo "[$timestamp] 告警: 测试失败" >> "$ROOT_DIR/.monitoring/monitor.log"
        send_alert "测试失败"
    fi
    
    echo "[$timestamp] 检查完成" >> "$ROOT_DIR/.monitoring/monitor.log"
}

check_specific() {
    log_info "执行特定检查"
    
    # 1. 检查目录结构
    log_info "检查目录结构..."
    if bash "$ROOT_DIR/scripts/health-check.sh" check-structure >/dev/null 2>&1; then
        log_success "目录结构检查通过"
    else
        log_error "目录结构检查失败"
    fi
    
    # 2. 检查依赖
    log_info "检查依赖..."
    if bash "$ROOT_DIR/scripts/health-check.sh" check-dependencies >/dev/null 2>&1; then
        log_success "依赖检查通过"
    else
        log_error "依赖检查失败"
    fi
    
    # 3. 检查配置
    log_info "检查配置..."
    if bash "$ROOT_DIR/scripts/health-check.sh" check-configuration >/dev/null 2>&1; then
        log_success "配置检查通过"
    else
        log_error "配置检查失败"
    fi
    
    # 4. 检查测试
    log_info "检查测试..."
    if bash "$ROOT_DIR/scripts/health-check.sh" check-tests >/dev/null 2>&1; then
        log_success "测试检查通过"
    else
        log_error "测试检查失败"
    fi
    
    # 5. 检查质量
    log_info "检查质量..."
    if bash "$ROOT_DIR/scripts/health-check.sh" check-quality >/dev/null 2>&1; then
        log_success "质量检查通过"
    else
        log_error "质量检查失败"
    fi
}

send_alert() {
    local message="$1"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    # 记录告警
    echo "[$timestamp] 告警: $message" >> "$ROOT_DIR/.monitoring/alerts.log"
    
    # 发送邮件告警（如果配置了）
    if [[ -n "${ALERT_EMAIL:-}" ]]; then
        echo "告警: $message" | mail -s "Global Dev Kit 告警" "$ALERT_EMAIL" 2>/dev/null || true
    fi
    
    # 发送webhook告警（如果配置了）
    if [[ -n "${ALERT_WEBHOOK:-}" ]]; then
        curl -X POST -H "Content-Type: application/json" -d "{\"text\": \"告警: $message\"}" "$ALERT_WEBHOOK" 2>/dev/null || true
    fi
}

generate_report() {
    log_info "生成监控报告"
    
    local report_file="$ROOT_DIR/.monitoring/report-$(date +%Y%m%d%H%M%S).md"
    
    cat > "$report_file" <<EOF
# 监控报告

## 报告信息
- 生成时间: $(date)
- 报告周期: 最近24小时

## 系统状态
- 磁盘使用率: $(df -h "$ROOT_DIR" | awk 'NR==2 {print $5}')
- 内存使用率: $(free | awk 'NR==2 {printf "%.0f", $3*100/$2}')%
- CPU负载: $(uptime | awk -F'load average:' '{print $2}')

## 健康检查
- 目录结构: $(bash "$ROOT_DIR/scripts/health-check.sh" check-structure >/dev/null 2>&1 && echo "通过" || echo "失败")
- 依赖检查: $(bash "$ROOT_DIR/scripts/health-check.sh" check-dependencies >/dev/null 2>&1 && echo "通过" || echo "失败")
- 配置检查: $(bash "$ROOT_DIR/scripts/health-check.sh" check-configuration >/dev/null 2>&1 && echo "通过" || echo "失败")
- 测试检查: $(bash "$ROOT_DIR/scripts/health-check.sh" check-tests >/dev/null 2>&1 && echo "通过" || echo "失败")
- 质量检查: $(bash "$ROOT_DIR/scripts/health-check.sh" check-quality >/dev/null 2>&1 && echo "通过" || echo "失败")

## 测试状态
- 测试用例: $(bash "$ROOT_DIR/tests/run_all.sh" 2>&1 | grep -E "Total:|Passed:|Failed:" | tail -3)

## 告警记录
$(if [[ -f "$ROOT_DIR/.monitoring/alerts.log" ]]; then
    echo "最近告警:"
    tail -10 "$ROOT_DIR/.monitoring/alerts.log"
else
    echo "无告警记录"
fi)

## 建议
1. 定期运行健康检查
2. 监控磁盘和内存使用
3. 及时处理告警
4. 定期备份数据
EOF
    
    log_success "监控报告已生成: $report_file"
}

main() {
    [[ $# -lt 1 ]] && { usage; exit 1; }
    local command="$1"; shift
    local interval=60 threshold=80 email="" webhook=""
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --interval) interval="$2"; shift 2 ;;
            --threshold) threshold="$2"; shift 2 ;;
            --email) email="$2"; shift 2 ;;
            --webhook) webhook="$2"; shift 2 ;;
            -h|--help) usage; exit 0 ;;
            *) log_error "未知参数: $1"; usage; exit 1 ;;
        esac
    done
    
    export ALERT_EMAIL="$email"
    export ALERT_WEBHOOK="$webhook"
    
    case "$command" in
        start) start_monitoring "$interval" ;;
        stop) stop_monitoring ;;
        status) show_status ;;
        check) check_specific ;;
        alert) send_alert "手动告警测试" ;;
        report) generate_report ;;
        *) log_error "未知命令: $command"; usage; exit 1 ;;
    esac
}

main "$@"
