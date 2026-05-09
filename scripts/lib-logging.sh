#!/usr/bin/env bash
# ============================================================================
# lib-logging.sh — 公共日志函数库
#
# 职责: 提供统一的日志输出函数
# 使用: source "$(dirname "${BASH_SOURCE[0]}")/lib-logging.sh"
# ============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
  echo -e "${CYAN}[INFO]${NC} $*"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $*" >&2
}

# 带时间戳的日志函数
log_info_ts() {
  echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]${NC} $*"
}

log_success_ts() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS]${NC} $*"
}

log_warning_ts() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $*"
}

log_error_ts() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $*" >&2
}

# 错误退出函数
fail() {
  log_error "$@"
  exit 1
}

# 检查命令是否存在
check_command() {
  local cmd="$1"
  if ! command -v "$cmd" &>/dev/null; then
    log_error "命令 '$cmd' 未找到，请先安装"
    return 1
  fi
  return 0
}

# 检查文件是否存在
check_file() {
  local file="$1"
  local description="${2:-文件}"
  if [[ ! -f "$file" ]]; then
    log_error "$description 不存在: $file"
    return 1
  fi
  return 0
}

# 检查目录是否存在
check_dir() {
  local dir="$1"
  local description="${2:-目录}"
  if [[ ! -d "$dir" ]]; then
    log_error "$description 不存在: $dir"
    return 1
  fi
  return 0
}

# 创建目录（如果不存在）
ensure_dir() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then
    mkdir -p "$dir"
    log_info "创建目录: $dir"
  fi
}

# 备份文件
backup_file() {
  local file="$1"
  local backup="${file}.backup.$(date '+%Y%m%d_%H%M%S')"
  if [[ -f "$file" ]]; then
    cp "$file" "$backup"
    log_info "备份文件: $file -> $backup"
  fi
}

# 清理临时文件
cleanup() {
  local files=("$@")
  for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
      rm -f "$file"
      log_info "清理临时文件: $file"
    fi
  done
}

# 显示帮助信息
show_help() {
  local script_name="$1"
  local description="$2"
  local usage="$3"
  
  cat <<EOF
$script_name — $description

用法: $usage

选项:
  -h, --help     显示此帮助信息
  -v, --verbose  详细输出
  -n, --dry-run  仅预览，不实际执行
  -f, --force    强制执行，跳过确认

示例:
  请参考文档或使用 --help 查看具体用法
EOF
}

# 解析通用参数
parse_common_args() {
  local args=("$@")
  VERBOSE=false
  DRY_RUN=false
  FORCE=false
  
  for arg in "${args[@]}"; do
    case "$arg" in
      -v|--verbose)
        VERBOSE=true
        ;;
      -n|--dry-run)
        DRY_RUN=true
        ;;
      -f|--force)
        FORCE=true
        ;;
      -h|--help)
        return 1
        ;;
    esac
  done
  
  return 0
}

# 详细日志（仅在 verbose 模式下输出）
log_verbose() {
  if [[ "$VERBOSE" == "true" ]]; then
    log_info "$@"
  fi
}

# 确认操作
confirm() {
  local message="$1"
  local default="${2:-n}"
  
  if [[ "$FORCE" == "true" ]]; then
    return 0
  fi
  
  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "[DRY-RUN] $message"
    return 1
  fi
  
  read -p "$message (y/N): " answer
  answer="${answer:-$default}"
  
  if [[ "$answer" =~ ^[Yy]$ ]]; then
    return 0
  else
    return 1
  fi
}

# 执行命令（支持 dry-run）
run_cmd() {
  local cmd="$*"
  
  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "[DRY-RUN] $cmd"
    return 0
  fi
  
  if [[ "$VERBOSE" == "true" ]]; then
    log_info "执行: $cmd"
  fi
  
  eval "$cmd"
}

# 检查依赖
check_dependencies() {
  local deps=("$@")
  local missing=()
  
  for dep in "${deps[@]}"; do
    if ! command -v "$dep" &>/dev/null; then
      missing+=("$dep")
    fi
  done
  
  if [[ ${#missing[@]} -gt 0 ]]; then
    log_error "缺少以下依赖: ${missing[*]}"
    log_error "请先安装这些依赖"
    return 1
  fi
  
  return 0
}

# 版本比较
version_compare() {
  local version1="$1"
  local version2="$2"
  
  if [[ "$version1" == "$version2" ]]; then
    return 0
  fi
  
  local IFS=.
  local i v1=($version1) v2=($version2)
  
  for ((i=0; i<${#v1[@]}; i++)); do
    if [[ -z "${v2[i]}" ]]; then
      return 1
    fi
    if ((10#${v1[i]} > 10#${v2[i]})); then
      return 1
    fi
    if ((10#${v1[i]} < 10#${v2[i]})); then
      return 2
    fi
  done
  
  if [[ ${#v1[@]} -lt ${#v2[@]} ]]; then
    return 2
  fi
  
  return 0
}

# 生成随机字符串
random_string() {
  local length="${1:-8}"
  tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c "$length"
}

# 检查是否为 root 用户
is_root() {
  [[ $EUID -eq 0 ]]
}

# 检查操作系统类型
get_os() {
  case "$(uname -s)" in
    Linux*)     echo "linux";;
    Darwin*)    echo "macos";;
    CYGWIN*)    echo "windows";;
    MINGW*)     echo "windows";;
    *)          echo "unknown";;
  esac
}

# 检查架构
get_arch() {
  case "$(uname -m)" in
    x86_64*)    echo "amd64";;
    aarch64*)   echo "arm64";;
    armv7*)     echo "armv7";;
    *)          echo "unknown";;
  esac
}
