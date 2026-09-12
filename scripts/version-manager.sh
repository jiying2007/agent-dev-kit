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
agent-dev-kit version manager

Usage:
  ./scripts/version-manager.sh <command> [options]

Commands:
  current                Show canonical manifest version
  verify                 Verify release version identity is synchronized
  lock                   Synchronize and lock a version
  unlock                 Remove .version-lock
  upgrade                Upgrade synchronized version identity
  compare                Compare two versions
  changelog              Generate a standalone changelog draft

Options:
  --version <version>    Version number
  --target <target>      Target version
  --force                Allow upgrade while .version-lock exists
  -h, --help             Show help

Examples:
  ./scripts/version-manager.sh current
  ./scripts/version-manager.sh verify
  ./scripts/version-manager.sh lock --version 5.1.0
  ./scripts/version-manager.sh upgrade --target 5.1.0 --force
USAGE
}

get_current_version() {
    python3 - "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
version = manifest.get("version")
if not isinstance(version, str) or not version:
    raise SystemExit("manifest.json version is missing or invalid")
print(version)
PY
}

verify_version() {
    python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
version = manifest.get("version")
if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", version):
    raise SystemExit("manifest.json version is missing or is not SemVer")

checks = {
    "pyproject.toml": (root / "pyproject.toml", rf'(?m)^version\s*=\s*["\']{re.escape(version)}["\']\s*$'),
    "src/agent_dev_kit/__init__.py": (
        root / "src" / "agent_dev_kit" / "__init__.py",
        rf'(?m)^__version__\s*=\s*["\']{re.escape(version)}["\']\s*$',
    ),
    ".version-lock": (root / ".version-lock", rf'(?m)^version:\s*{re.escape(version)}\s*$'),
    "README.md": (root / "README.md", rf'(?m)^当前版本：`{re.escape(version)}`'),
    "CONTEXT.md": (root / "CONTEXT.md", rf'(?m)^> 产品版本：{re.escape(version)}\s*$'),
}
failures: list[str] = []
for label, (path, pattern) in checks.items():
    if not path.is_file():
        failures.append(f"missing {label}")
        continue
    if re.search(pattern, path.read_text(encoding="utf-8")) is None:
        failures.append(f"version mismatch in {label}")

if failures:
    for failure in failures:
        print(f"[FAIL] {failure}", file=sys.stderr)
    raise SystemExit(1)
print(f"version identity verified: {version}")
PY
}

sync_version() {
    local target_version="$1"
    local actor="${ADK_VERSION_LOCKED_BY:-$(whoami)}"

    python3 - "$ROOT_DIR" "$target_version" "$actor" <<'PY'
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
target = sys.argv[2]
actor = sys.argv[3].strip()
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", target):
    raise SystemExit(f"invalid semantic version: {target}")
if not actor or "\n" in actor or "\r" in actor:
    raise SystemExit("version lock actor is invalid")


def replace_once(path: Path, pattern: str, replacement: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"unable to update {label}: expected exactly one version field")
    path.write_text(updated, encoding="utf-8")

manifest_path = root / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
current = manifest.get("version")
if not isinstance(current, str) or not current:
    raise SystemExit("manifest.json version is missing or invalid")
replace_once(
    manifest_path,
    r'^(\s*"version"\s*:\s*")[^"]+("\s*,\s*)$',
    rf'\g<1>{target}\g<2>',
    "manifest.json",
)
replace_once(
    root / "pyproject.toml",
    r'^(version\s*=\s*")[^"]+("\s*)$',
    rf'\g<1>{target}\g<2>',
    "pyproject.toml",
)
replace_once(
    root / "src" / "agent_dev_kit" / "__init__.py",
    r'^(__version__\s*=\s*")[^"]+("\s*)$',
    rf'\g<1>{target}\g<2>',
    "src/agent_dev_kit/__init__.py",
)
replace_once(
    root / "README.md",
    r'^(当前版本：`)[^`]+(`.*)$',
    rf'\g<1>{target}\g<2>',
    "README.md",
)
replace_once(
    root / "CONTEXT.md",
    r'^(> 产品版本：).+$',
    rf'\g<1>{target}',
    "CONTEXT.md",
)
locked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
(root / ".version-lock").write_text(
    f"version: {target}\nlocked_at: {locked_at}\nlocked_by: {actor}\n",
    encoding="utf-8",
)
print(f"version synchronized: {current} -> {target}")
PY
}

show_current_version() {
    local version
    version="$(get_current_version)"
    log_info "当前版本: $version"
    echo "$version"
}

lock_version() {
    local version="$1"
    log_info "同步并锁定版本: $version"
    sync_version "$version"
    verify_version
    log_success "版本已锁定: $version"
}

unlock_version() {
    log_info "解锁版本"
    if [[ -f "$ROOT_DIR/.version-lock" ]]; then
        rm -f "$ROOT_DIR/.version-lock"
        log_success "版本已解锁"
    else
        log_warning "版本锁定文件不存在"
    fi
}

upgrade_version() {
    local target_version="$1"
    local force="$2"
    local current_version
    current_version="$(get_current_version)"

    log_info "升级版本: ${current_version} -> ${target_version}"
    if [[ -f "$ROOT_DIR/.version-lock" && "$force" != "true" ]]; then
        log_error "版本已锁定，使用 --force 执行受控升级"
        return 1
    fi
    if [[ "$current_version" == "$target_version" ]]; then
        verify_version
        log_warning "目标版本与当前版本相同"
        return 0
    fi
    sync_version "$target_version"
    verify_version
    log_success "版本升级完成: ${current_version} -> ${target_version}"
}

compare_versions() {
    local version1="$1"
    local version2="$2"
    if [[ "$version1" == "$version2" ]]; then
        echo "$version1 == $version2"
    elif [[ "$(printf '%s\n%s\n' "$version1" "$version2" | sort -V | head -n1)" == "$version1" ]]; then
        echo "$version1 < $version2"
    else
        echo "$version1 > $version2"
    fi
}

format_recent_changes() {
    local changes="$1"
    local pattern="$2"
    local lines
    lines="$(printf '%s\n' "$changes" | awk -v pattern="$pattern" '$0 ~ pattern && count < 10 {print "- " $0; count++}')"
    if [[ -n "$lines" ]]; then
        printf '%s\n' "$lines"
    else
        printf '%s\n' "- 无自动识别条目。"
    fi
}

generate_changelog() {
    local version="$1"
    local changelog_file="$ROOT_DIR/CHANGELOG-$version.md"
    local release_date
    local maintainer
    local recent_changes
    release_date="$(date +%Y-%m-%d)"
    maintainer="${ADK_VERSION_LOCKED_BY:-$(whoami)}"
    recent_changes="$(git -C "$ROOT_DIR" log --oneline --no-merges -n 20 2>/dev/null || true)"

    cat > "$changelog_file" <<EOF
# 变更日志 - $version

## 版本信息
- 版本号: $version
- 发布日期: $release_date
- 维护者: $maintainer

## 变更内容

### 新增功能
$(format_recent_changes "$recent_changes" ' feat([(]|:)')

### 改进优化
$(format_recent_changes "$recent_changes" ' (docs|refactor|perf|chore)([(]|:)')

### 修复问题
$(format_recent_changes "$recent_changes" ' fix([(]|:)')

### 已知问题
- 未在自动生成阶段登记新的已知问题；发布前以验证报告和 issue 跟踪为准。
EOF
    log_success "变更日志已生成: $changelog_file"
}

main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local command="$1"
    shift
    local version=""
    local target=""
    local force="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --version)
                [[ $# -ge 2 ]] || { log_error "--version 缺少值"; exit 1; }
                version="$2"
                shift 2
                ;;
            --target)
                [[ $# -ge 2 ]] || { log_error "--target 缺少值"; exit 1; }
                target="$2"
                shift 2
                ;;
            --force)
                force="true"
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
        current)
            show_current_version
            ;;
        verify)
            verify_version
            ;;
        lock)
            [[ -n "$version" ]] || { log_error "缺少 --version 参数"; exit 1; }
            lock_version "$version"
            ;;
        unlock)
            unlock_version
            ;;
        upgrade)
            [[ -n "$target" ]] || { log_error "缺少 --target 参数"; exit 1; }
            upgrade_version "$target" "$force"
            ;;
        compare)
            [[ -n "$version" && -n "$target" ]] || { log_error "缺少 --version 或 --target 参数"; exit 1; }
            compare_versions "$version" "$target"
            ;;
        changelog)
            version="${version:-$(get_current_version)}"
            generate_changelog "$version"
            ;;
        *)
            log_error "未知命令: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
