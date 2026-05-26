#!/usr/bin/env bash
set -euo pipefail

# 加载公共日志库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib-logging.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

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
# agent-dev-kit v$version 发布说明

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
cd agent-dev-kit

# 验证安装
bash scripts/health-check.sh check-all

# 运行测试
bash tests/run_all.sh
\`\`\`

## 快速开始
\`\`\`bash
# 查看版本
bash scripts/version-manager.sh current

# 创建声明式资产仓库备份
bash scripts/backup-rollback.sh backup --target /tmp/adk-runtime

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

    local archive="$ROOT_DIR/dist/agent-dev-kit-${version}.tar.gz"
    tar -czf "$archive" -C "$ROOT_DIR/dist" "$version"
    log_success "发布包构建完成: $archive"
}

publish_release() {
    local version="$1"
    local target="$2"
    local dry_run="$3"
    log_info "发布版本: $version target=${target}"
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 跳过真实发布"
        return 0
    fi
    [[ -f "$ROOT_DIR/dist/agent-dev-kit-${version}.tar.gz" ]] || build_release "$version"
    log_success "发布完成: $version"
}

rollback_release() {
    local version="$1"
    local dry_run="$2"
    log_warning "回滚发布: $version"
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 跳过真实回滚"
        return 0
    fi
    bash "$ROOT_DIR/scripts/version-manager.sh" unlock || true
    log_success "回滚流程完成"
}

show_status() {
    log_info "发布状态"
    echo "current_version=$(bash "$ROOT_DIR/scripts/version-manager.sh" current 2>/dev/null || echo unknown)"
    echo "dist_dir=$ROOT_DIR/dist"
}

main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local command="$1"
    shift
    local version=""
    local target="local"
    local force="false"
    local dry_run="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --version)
                version="$2"
                shift 2
                ;;
            --target)
                target="$2"
                shift 2
                ;;
            --force)
                force="true"
                shift
                ;;
            --dry-run)
                dry_run="true"
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
        prepare)
            [[ -n "$version" ]] || { log_error "缺少 --version 参数"; exit 1; }
            prepare_release "$version" "$dry_run" "$force"
            ;;
        validate)
            [[ -n "$version" ]] || { log_error "缺少 --version 参数"; exit 1; }
            validate_release "$version"
            ;;
        build)
            [[ -n "$version" ]] || { log_error "缺少 --version 参数"; exit 1; }
            build_release "$version"
            ;;
        publish)
            [[ -n "$version" ]] || { log_error "缺少 --version 参数"; exit 1; }
            publish_release "$version" "$target" "$dry_run"
            ;;
        rollback)
            [[ -n "$version" ]] || { log_error "缺少 --version 参数"; exit 1; }
            rollback_release "$version" "$dry_run"
            ;;
        status)
            show_status
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "未知命令: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
