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
版本发布管理脚本

Usage:
  ./scripts/release-manager.sh <command> [options]

Commands:
  prepare                准备发布
  validate               验证发布条件
  build                  构建发布包
  publish                发布版本
  rollback               回滚发布
  status                 查看发布状态

Options:
  --version <version>    版本号
  --target <target>      发布目标
  --force                强制执行
  --dry-run              模拟运行
  -h, --help             显示帮助

Examples:
  ./scripts/release-manager.sh prepare --version 1.0.0
  ./scripts/release-manager.sh validate --version 1.0.0
  ./scripts/release-manager.sh build --version 1.0.0
  ./scripts/release-manager.sh publish --version 1.0.0 --target production
USAGE
}

prepare_release() {
    local version="$1" dry_run="$2" force="$3"
    log_info "准备发布版本: $version"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 模拟准备发布"
    fi
    
    # 1. 验证版本格式
    if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "版本格式错误: $version (应为 x.y.z)"
        return 1
    fi
    
    # 2. 检查工作目录
    if [[ -n "$(git status --porcelain)" ]]; then
        log_warning "工作目录有未提交的更改"
        if [[ "$dry_run" != "true" ]]; then
            if [[ "${force:-}" != "true" ]]; then
                echo "[FAIL] --force required" >&2
                exit 1
            fi
        fi
    fi
    
    # 3. 创建发布分支
    local release_branch="release/$version"
    if [[ "$dry_run" != "true" ]]; then
        git checkout -b "$release_branch" 2>/dev/null || git checkout "$release_branch"
    fi
    
    # 4. 更新版本号
    if [[ "$dry_run" != "true" ]]; then
        bash "$ROOT_DIR/scripts/version-manager.sh" lock --version "$version"
    fi
    
    # 5. 生成变更日志
    if [[ "$dry_run" != "true" ]]; then
        bash "$ROOT_DIR/scripts/version-manager.sh" changelog
    fi
    
    log_success "发布准备完成: $version"
    return 0
}

validate_release() {
    local version="$1"
    log_info "验证发布条件: $version"
    local errors=()
    
    # 1. 检查版本格式
    if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        errors+=("版本格式错误: $version")
    fi
    
    # 2. 运行测试
    log_info "运行测试..."
    if ! bash "$ROOT_DIR/tests/run_all.sh" >/dev/null 2>&1; then
        errors+=("测试失败")
    fi
    
    # 3. 运行健康检查
    log_info "运行健康检查..."
    if ! bash "$ROOT_DIR/scripts/health-check.sh" check-all >/dev/null 2>&1; then
        errors+=("健康检查失败")
    fi
    
    # 4. 运行质量门禁
    log_info "运行质量门禁..."
    if ! bash "$ROOT_DIR/scripts/quality-gate-check.sh" check-all >/dev/null 2>&1; then
        errors+=("质量门禁失败")
    fi
    
    # 5. 检查文档完整性
    log_info "检查文档完整性..."
    local required_docs=("docs/quick-start.md" "docs/usage.md" "docs/commands.md" "docs/troubleshooting.md")
    for doc in "${required_docs[@]}"; do
        if [[ ! -f "$ROOT_DIR/$doc" ]]; then
            errors+=("缺失文档: $doc")
        fi
    done
    
    # 6. 检查脚本完整性
    log_info "检查脚本完整性..."
    local required_scripts=("scripts/health-check.sh" "scripts/backup-rollback.sh" "scripts/version-manager.sh" "scripts/release-manager.sh")
    for script in "${required_scripts[@]}"; do
        if [[ ! -f "$ROOT_DIR/$script" ]]; then
            errors+=("缺失脚本: $script")
        fi
    done
    
    if [[ ${#errors[@]} -eq 0 ]]; then
        log_success "发布验证通过: $version"
        return 0
    else
        log_error "发布验证失败:"
        for error in "${errors[@]}"; do echo "  - $error"; done
        return 1
    fi
}

build_release() {
    local version="$1"
    log_info "构建发布包: $version"
    
    local build_dir="$ROOT_DIR/dist/$version"
    mkdir -p "$build_dir"
    
    # 1. 复制核心文件
    log_info "复制核心文件..."
    cp -r "$ROOT_DIR/agents" "$build_dir/"
    cp -r "$ROOT_DIR/skills" "$build_dir/"
    cp -r "$ROOT_DIR/optional-skills" "$build_dir/"
    cp -r "$ROOT_DIR/scripts" "$build_dir/"
    cp -r "$ROOT_DIR/tests" "$build_dir/"
    cp -r "$ROOT_DIR/docs" "$build_dir/"
    cp -r "$ROOT_DIR/templates" "$build_dir/"
    cp "$ROOT_DIR/manifest.yaml" "$build_dir/"
    cp "$ROOT_DIR/README.md" "$build_dir/"
    cp "$ROOT_DIR/CONTEXT.md" "$build_dir/"
    cp "$ROOT_DIR/AGENTS.md" "$build_dir/"
    
    # 2. 创建发布说明
    log_info "创建发布说明..."
    cat > "$build_dir/RELEASE-NOTES.md" <<EOF
# Global Dev Kit v$version 发布说明

## 版本信息
- 版本号: $version
- 发布日期: $(date +%Y-%m-%d)
- 构建时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## 主要特性
- 完整的文档体系
- 生产部署能力
- 质量保证机制
- 版本管理工具

## 安装方法
\`\`\`bash
# 克隆仓库
git clone <repository-url>
cd global-dev-kit

# 验证安装
bash scripts/health-check.sh check-all

# 运行测试
bash tests/run_all.sh
\`\`\`

## 快速开始
\`\`\`bash
# 查看版本
bash scripts/version-manager.sh current

# 创建备份
bash scripts/backup-rollback.sh backup --target ~/.codex

# 健康检查
bash scripts/health-check.sh check-all
\`\`\`

## 相关链接
- 快速入门: docs/quick-start.md
- 使用指南: docs/usage.md
- 故障排除: docs/troubleshooting.md
- 最佳实践: docs/best-practices.md

## 反馈
如有问题或建议，请提交Issue。
EOF
    
    # 3. 创建安装脚本
    log_info "创建安装脚本..."
    cat > "$build_dir/install.sh" <<'INSTALLEOF'
#!/usr/bin/env bash
set -euo pipefail

echo "安装 Global Dev Kit..."

# 检查依赖
if ! command -v bash &> /dev/null; then
    echo "错误: 未安装Bash"
    exit 1
fi

# 设置权限
chmod +x scripts/*.sh
chmod +x tests/*.sh

# 运行健康检查
echo "运行健康检查..."
if bash scripts/health-check.sh check-all; then
    echo "安装成功！"
    echo ""
    echo "快速开始:"
    echo "  bash scripts/version-manager.sh current"
    echo "  bash scripts/health-check.sh check-all"
    echo "  bash tests/run_all.sh"
else
    echo "警告: 健康检查失败，请检查环境"
fi
INSTALLEOF
    chmod +x "$build_dir/install.sh"
    
    # 4. 创建压缩包
    log_info "创建压缩包..."
    local archive_name="global-dev-kit-$version.tar.gz"
    tar -czf "$ROOT_DIR/dist/$archive_name" -C "$ROOT_DIR/dist" "$version"
    
    log_success "发布包构建完成: $ROOT_DIR/dist/$archive_name"
    return 0
}

publish_release() {
    local version="$1" target="$2" force="$3"
    log_info "发布版本: $version -> $target"
    
    # 1. 验证发布包
    local archive_name="global-dev-kit-$version.tar.gz"
    if [[ ! -f "$ROOT_DIR/dist/$archive_name" ]]; then
        log_error "发布包不存在: $archive_name"
        return 1
    fi
    
    # 2. 备份当前版本
    if [[ "$target" == "production" ]]; then
        log_info "创建生产环境备份..."
        bash "$ROOT_DIR/scripts/backup-rollback.sh" backup --target "$target"
    fi
    
    # 3. 部署到目标环境
    log_info "部署到目标环境: $target"
    if [[ "$target" == "production" ]]; then
        # 生产环境部署
        local deploy_dir="/opt/global-dev-kit"
        mkdir -p "$deploy_dir"
        tar -xzf "$ROOT_DIR/dist/$archive_name" -C "$deploy_dir"
        log_success "部署完成: $deploy_dir"
    elif [[ "$target" == "staging" ]]; then
        # 预发布环境部署
        local deploy_dir="/opt/global-dev-kit-staging"
        mkdir -p "$deploy_dir"
        tar -xzf "$ROOT_DIR/dist/$archive_name" -C "$deploy_dir"
        log_success "部署完成: $deploy_dir"
    else
        log_error "未知目标环境: $target"
        return 1
    fi
    
    # 4. 验证部署
    log_info "验证部署..."
    if [[ -f "$deploy_dir/scripts/health-check.sh" ]]; then
        bash "$deploy_dir/scripts/health-check.sh" check-all
    fi
    
    log_success "发布完成: $version -> $target"
    return 0
}

rollback_release() {
    local version="$1" target="$2"
    log_info "回滚发布: $version -> $target"
    
    # 1. 创建备份
    log_info "创建当前版本备份..."
    bash "$ROOT_DIR/scripts/backup-rollback.sh" backup --target "$target"
    
    # 2. 恢复备份
    log_info "恢复备份..."
    bash "$ROOT_DIR/scripts/backup-rollback.sh" restore --target "$target" --version "$version" --force
    
    log_success "回滚完成: $version"
    return 0
}

show_status() {
    log_info "发布状态:"
    echo ""
    echo "当前版本:"
    bash "$ROOT_DIR/scripts/version-manager.sh" current
    echo ""
    echo "发布包:"
    ls -la "$ROOT_DIR/dist/" 2>/dev/null || echo "  无发布包"
    echo ""
    echo "备份:"
    bash "$ROOT_DIR/scripts/backup-rollback.sh" list --target ~/.codex 2>/dev/null || echo "  无备份"
}

main() {
    [[ $# -lt 1 ]] && { usage; exit 1; }
    local command="$1"; shift
    local version="" target="" force="false" dry_run="false"
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --version) version="$2"; shift 2 ;;
            --target) target="$2"; shift 2 ;;
            --force) force="true"; shift ;;
            --dry-run) dry_run="true"; shift ;;
            -h|--help) usage; exit 0 ;;
            *) log_error "未知参数: $1"; usage; exit 1 ;;
        esac
    done
    
    case "$command" in
        prepare) [[ -z "$version" ]] && { log_error "缺少--version"; exit 1; }; prepare_release "$version" "$dry_run" "$force" ;;
        validate) [[ -z "$version" ]] && { log_error "缺少--version"; exit 1; }; validate_release "$version" ;;
        build) [[ -z "$version" ]] && { log_error "缺少--version"; exit 1; }; build_release "$version" ;;
        publish) [[ -z "$version" || -z "$target" ]] && { log_error "缺少参数"; exit 1; }; publish_release "$version" "$target" "$force" ;;
        rollback) [[ -z "$version" || -z "$target" ]] && { log_error "缺少参数"; exit 1; }; rollback_release "$version" "$target" ;;
        status) show_status ;;
        *) log_error "未知命令: $command"; usage; exit 1 ;;
    esac
}

main "$@"
