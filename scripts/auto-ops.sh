#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/lib-logging.sh"

# This CLI is intentionally report-only; no unreachable mutating branches remain.
usage() {
    cat <<'USAGE'
ADK 维护观测（只读）

Usage:
  ./scripts/auto-ops.sh <daily|weekly|monthly|cleanup|optimize|security> [options]

Options:
  --dry-run       显式只读（也是默认行为）
  --summary-json  输出低 token 状态
  --apply         已禁用；返回 blocked / exit 2
  --force         仅搭配 --apply，仍不会允许写入
  -h, --help      查看帮助
USAGE
}

json_string() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//$'\n'/\\n}"
    printf '"%s"' "$value"
}

summary_json() {
    local command="$1" status="pass"
    case "$command" in
        daily|weekly|monthly|cleanup|optimize|security) ;;
        *) status="fail" ;;
    esac
    printf '{"schema_version":1,"status":%s,"command":%s,"apply":0,"writes":"none","target":%s}\n' \
        "$(json_string "$status")" "$(json_string "$command")" "$(json_string "$ROOT_DIR")"
    [[ "$status" == "pass" ]]
}

security_check() {
    log_info "安全检查"
    
    local issues=()
    
    # 1. 检查文件权限
    log_info "检查文件权限"
    local world_writable=$(find "$ROOT_DIR" -type f -perm -o+w 2>/dev/null | wc -l)
    if [[ "$world_writable" -gt 0 ]]; then
        issues+=("发现 $world_writable 个世界可写文件")
    fi
    
    # 2. 检查敏感文件
    log_info "检查敏感文件"
    local sensitive_files=(".env" "*.key" "*.pem" "*.p12")
    for pattern in "${sensitive_files[@]}"; do
        local found=$(find "$ROOT_DIR" -name "$pattern" -type f 2>/dev/null | wc -l)
        if [[ "$found" -gt 0 ]]; then
            issues+=("发现 $found 个敏感文件: $pattern")
        fi
    done
    
    # 3. 检查脚本安全
    log_info "检查脚本安全"
    local scripts_with_sudo=$(grep -r "sudo" "$ROOT_DIR/scripts" 2>/dev/null | wc -l)
    if [[ "$scripts_with_sudo" -gt 0 ]]; then
        issues+=("发现 $scripts_with_sudo 个脚本使用sudo")
    fi
    
    if [[ ${#issues[@]} -eq 0 ]]; then
        log_success "安全检查通过"
    else
        log_warning "安全检查发现问题:"
        for issue in "${issues[@]}"; do echo "  - $issue"; done
    fi
}

main() {
    [[ $# -gt 0 ]] || { usage; exit 1; }
    local command="$1"
    shift
    local apply=0 force=0 summary=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run) shift ;;
            --apply) apply=1; shift ;;
            --force) force=1; shift ;;
            --summary-json) summary=1; shift ;;
            -h|--help) usage; exit 0 ;;
            *) log_error "未知参数: $1"; usage; exit 1 ;;
        esac
    done
    [[ "$force" -eq 0 || "$apply" -eq 1 ]] || {
        log_error "--force 必须与 --apply 同时使用"
        exit 1
    }
    if [[ "$apply" -eq 1 ]]; then
        if [[ "$summary" -eq 1 ]]; then
            printf '%s\n' '{"schema":"adk-maintenance-plan/v1","status":"blocked","read_only":true,"applied":false,"execution_supported":false,"reason":"reviewed-bounded-execution-contract-required"}'
        else
            log_error "未提供受审查维护写入合同；当前仅支持 report-only，--apply 已阻断"
        fi
        exit 2
    fi
    case "$command" in
        cleanup|optimize)
            # This branch imports typed ADK Python; shell-only operations remain independent.
            # shellcheck source=./lib-python-runtime.sh
            source "$SCRIPT_DIR/lib-python-runtime.sh"
            adk_select_python
            local -a args=(--root "$ROOT_DIR" --level basic)
            [[ "$summary" -eq 0 ]] || args+=(--summary-json)
            PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
                "${PYTHON_BIN}" -m agent_dev_kit.maintenance_plan "${args[@]}"
            ;;
        daily|weekly|monthly|security)
            if [[ "$summary" -eq 1 ]]; then
                summary_json "$command"
            elif [[ "$command" == security ]]; then
                security_check
            else
                case "$command" in
                    daily) log_info "执行每日运维（report-only）" ;;
                    weekly) log_info "执行每周运维（report-only）" ;;
                    monthly) log_info "执行每月运维（report-only）" ;;
                esac
                printf '%s\n' "[PLAN] 仅提供观测建议，不运行清理、备份、提权、写报告或定时任务；--apply 会阻断。"
            fi
            ;;
        *) log_error "未知命令: $command"; usage; exit 1 ;;
    esac
}
main "$@"
