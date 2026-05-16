#!/usr/bin/env bash
set -euo pipefail

# 加载公共日志库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib-logging.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

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

    log_success "监控配置已写入: $ROOT_DIR/.monitoring/config.json"
}

stop_monitoring() {
    log_info "停止监控"
    rm -f "$ROOT_DIR/.monitoring/config.json"
    log_success "监控已停止"
}

show_status() {
    if [[ -f "$ROOT_DIR/.monitoring/config.json" ]]; then
        log_info "监控状态: running"
        cat "$ROOT_DIR/.monitoring/config.json"
    else
        log_info "监控状态: stopped"
    fi
}

run_check() {
    local threshold="$1"
    local usage
    usage="$(df -h "$ROOT_DIR" | awk 'NR==2 {gsub("%","",$5); print $5}')"
    log_info "磁盘使用率: ${usage}% (threshold=${threshold})"
    if [[ "$usage" -gt "$threshold" ]]; then
        log_warning "磁盘使用率超过阈值"
        return 1
    fi
    log_success "监控检查通过"
}

send_alert() {
    local email="$1"
    local webhook="$2"
    log_warning "告警通道未配置为真实发送，仅输出预览"
    [[ -n "$email" ]] && echo "email=${email}"
    [[ -n "$webhook" ]] && echo "webhook=${webhook}"
}

generate_report() {
    mkdir -p "$ROOT_DIR/.monitoring"
    local report="$ROOT_DIR/.monitoring/report-$(date +%Y%m%d).md"
    cat > "$report" <<EOF
# 监控报告

- 生成时间: $(date)
- 磁盘使用率: $(df -h "$ROOT_DIR" | awk 'NR==2 {print $5}')
- 当前版本: $(bash "$ROOT_DIR/scripts/version-manager.sh" current 2>/dev/null || echo unknown)
EOF
    log_success "监控报告已生成: $report"
}

main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local command="$1"
    shift
    local interval="60"
    local threshold="80"
    local email=""
    local webhook=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --interval)
                interval="$2"
                shift 2
                ;;
            --threshold)
                threshold="$2"
                shift 2
                ;;
            --email)
                email="$2"
                shift 2
                ;;
            --webhook)
                webhook="$2"
                shift 2
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
        start) start_monitoring "$interval" ;;
        stop) stop_monitoring ;;
        status) show_status ;;
        check) run_check "$threshold" ;;
        alert) send_alert "$email" "$webhook" ;;
        report) generate_report ;;
        -h|--help) usage ;;
        *) log_error "未知命令: $command"; usage; exit 1 ;;
    esac
}

main "$@"
