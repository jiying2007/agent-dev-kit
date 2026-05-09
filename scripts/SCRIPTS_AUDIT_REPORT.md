# Scripts 层审计报告

审计日期: 2026-05-09
脚本总数: 24 个 (.sh 文件)
项目路径: /home/aiot03/aiot/llm_agent/agent-dev-kit/scripts

---

## 一、总览统计

| 检查项 | 结果 |
|--------|------|
| 语法检查 (bash -n) | 24/24 全部通过 |
| set -euo pipefail | 24/24 全部使用 |
| trap 错误捕获 | 0/24 使用 |
| usage/--help 支持 | 21/24 有 (3个缺失) |
| 重复函数定义 | 6 组重复 (log_* 系列最多) |
| 死代码函数 | 3 个 (lib_manifest 的是库导出，不计) |
| 隐式外部依赖 | rg 在 6 个脚本中使用 |
| 交互式 read | 0 个真正交互式 (全部是管道 read -r) |
| 破坏性操作 | 11 处 rm -rf，1 处 sed -i |

---

## 二、逐脚本审计表

| 脚本名 | 语法 | 参数(0-5) | 错误处理(0-5) | 重复函数 | 死代码 | 隐式依赖 | 交互read | 破坏操作 | 综合评分 |
|--------|------|-----------|---------------|----------|--------|----------|----------|----------|----------|
| auto-ops.sh | ✅ | 5 | 4 | 4 | 0 | 0 | 0 | 2 | 8.0 |
| backup-rollback.sh | ✅ | 5 | 4 | 3 | 0 | 0 | 0 | 1 | 8.5 |
| catalog_assets.sh | ✅ | 5 | 4 | 4 | 0 | 0 | 0 | 0 | 8.5 |
| check_change_governance.sh | ✅ | 3 | 4 | 0 | 0 | 2 | 0 | 0 | 8.0 |
| check_format.sh | ✅ | 1 | 4 | 0 | 0 | 2 | 0 | 0 | 7.0 |
| check_profile_coherence.sh | ✅ | 4 | 4 | 3 | 0 | 0 | 0 | 1 | 8.0 |
| check-terminology-consistency.sh | ✅ | 1 | 4 | 0 | 0 | 0 | 0 | 0 | 7.0 |
| convert_assets.sh | ✅ | 5 | 4 | 3 | 0 | 0 | 0 | 1 | 8.0 |
| devkit.sh | ✅ | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 9.0 |
| evidence_index.sh | ✅ | 4 | 4 | 0 | 0 | 1 | 0 | 0 | 8.5 |
| health-check.sh | ✅ | 5 | 4 | 4 | 1 | 1 | 0 | 0 | 7.5 |
| install_assets.sh | ✅ | 5 | 4 | 3 | 0 | 0 | 0 | 1 | 8.0 |
| lib_manifest.sh | ✅ | 2 | 4 | 0 | 0* | 0 | 0 | 0 | 8.5 |
| monitoring.sh | ✅ | 5 | 4 | 4 | 0 | 0 | 0 | 1 | 8.0 |
| openspec_bridge.sh | ✅ | 5 | 4 | 3 | 0 | 1 | 0 | 0 | 8.5 |
| performance.sh | ✅ | 5 | 4 | 4 | 1 | 0 | 0 | 3 | 7.5 |
| quality-gate-check.sh | ✅ | 5 | 4 | 4 | 1 | 0 | 0 | 0 | 8.0 |
| release-manager.sh | ✅ | 5 | 4 | 4 | 0 | 0 | 0 | 0 | 8.5 |
| security.sh | ✅ | 5 | 4 | 4 | 0 | 0 | 0 | 0 | 8.5 |
| skill_match.sh | ✅ | 5 | 4 | 3 | 0 | 0 | 0 | 0 | 8.5 |
| sync_codex_assets.sh | ✅ | 1 | 4 | 0 | 0 | 0 | 0 | 0 | 7.5 |
| validate_assets.sh | ✅ | 5 | 4 | 4 | 0 | 0 | 0 | 0 | 8.5 |
| version-manager.sh | ✅ | 5 | 4 | 4 | 0 | 0 | 0 | 2 | 8.0 |
| workflow.sh | ✅ | 5 | 4 | 3 | 0 | 1 | 0 | 0 | 8.5 |

> *lib_manifest.sh 是库文件，其函数被 6 个其他脚本 source 引用，不算死代码

---

## 三、问题详述

### 3.1 缺少 usage/--help 的脚本 (3个)

1. **check_format.sh** - 无 usage 函数，无 --help 处理
2. **check-terminology-consistency.sh** - 无 usage 函数，无 --help 处理
3. **sync_codex_assets.sh** - 仅是 install_assets.sh 的 exec 转发包装器

### 3.2 重复函数定义 (高重复)

以下函数在多个脚本中重复定义，应提取为公共库：

| 函数名 | 重复次数 | 涉及脚本 |
|--------|----------|----------|
| log_info() | 8 | auto-ops, backup-rollback, catalog, convert, health-check, monitoring, openspec, performance, quality-gate, release, security, skill_match, validate, version, workflow |
| log_warning() | 8 | 同上 |
| log_success() | 8 | 同上 |
| log_error() | 8 | 同上 |
| usage() | 20 | 除 lib_manifest/check_format/check-terminology/sync_codex 外全部 |
| main() | 9 | 9 个脚本 |
| generate_report() | 3 | monitoring, performance, security |
| fail() | 3 | convert, install, validate |

### 3.3 死代码 (确认)

| 脚本 | 函数 | 原因 |
|------|------|------|
| health-check.sh | log_warning() | 定义但从未调用 |
| performance.sh | log_warning() | 定义但从未调用 |
| quality-gate-check.sh | log_warning() | 定义但从未调用 |

### 3.4 隐式外部依赖 (rg)

`ripgrep (rg)` 在以下脚本中使用，但未检查是否安装：

| 脚本 | 用途 | 行号 |
|------|------|------|
| check_change_governance.sh | 检查变更治理文件内容 | L34, L43 |
| check_format.sh | CRLF/Tab 检查 | L18, L23 |
| evidence_index.sh | 检查 Evidence Index 段落 | L94 |
| openspec_bridge.sh | 检查未完成任务 | L119 |
| workflow.sh | 检查 ReviewReport/TestReport | L188 |
| health-check.sh | 作为依赖项检查 | L101 |

> 建议: 在脚本开头添加 `command -v rg >/dev/null 2>&1 || { echo "需要安装 ripgrep"; exit 1; }`

### 3.5 破坏性操作详情

| 脚本 | 操作 | 行号 | 风险等级 |
|------|------|------|----------|
| auto-ops.sh | rm -rf dist/ | L177 | 低 (临时目录) |
| auto-ops.sh | rm -rf .cache/ | L208 | 低 (缓存目录) |
| backup-rollback.sh | rm -rf $target | L81 | 中 (恢复操作) |
| check_profile_coherence.sh | rm -f temp文件 | L97 | 低 |
| convert_assets.sh | rm -rf $TARGET_DIR | L201 | 中 (输出目录) |
| install_assets.sh | rm -rf $dst | L170 | 中 (安装目录) |
| monitoring.sh | rm -f config.json | L79 | 低 |
| performance.sh | rm -rf .cache/ | L94 | 低 |
| performance.sh | rm -rf dist/ | L105 | 低 |
| performance.sh | rm -f .benchmark | L144 | 低 |
| version-manager.sh | sed -i manifest.yaml | L65 | 中 (修改主配置) |
| version-manager.sh | rm -f .version-lock | L85 | 低 |

### 3.6 交互式 read

所有 `read -r` 调用均为管道非交互式读取 (`while IFS= read -r ...`)，无真正的交互式阻塞。符合 CI/CD 友好要求。

---

## 四、评分标准说明

- 参数处理 (0-5): 0=无任何参数处理, 3=部分处理, 5=完整 usage+--help
- 错误处理 (0-5): 基准4分(set -euo pipefail), +1如有trap, -1如缺少关键检查
- 综合评分: 加权平均，考虑所有维度

---

## 五、综合评分: 8.1/10

### 优点
1. **100% 语法通过** - 所有脚本 bash -n 检查无错误
2. **100% set -euo pipefail** - 严格错误处理全覆盖
3. **零交互式阻塞** - 全部管道读取，CI/CD 友好
4. **统一命令入口** - devkit.sh 提供一致的 CLI 体验
5. **库文件设计** - lib_manifest.sh 被 6 个脚本 source 复用

### 改进建议 (按优先级)

**P0 - 必须修复:**
1. 为 check_format.sh 和 check-terminology-consistency.sh 添加 usage/--help
2. 为使用 rg 的脚本添加依赖检查 (command -v rg)

**P1 - 建议修复:**
3. 提取 log_info/log_warning/log_success/log_error 到公共库 (减少 ~120 行重复代码)
4. 删除 health-check.sh、performance.sh、quality-gate-check.sh 中未使用的 log_warning
5. 为 rm -rf 操作添加确认提示或 --force 参数

**P2 - 可选优化:**
6. 添加 trap 捕获 ERR 信号，提供更好的错误上下文
7. version-manager.sh 的 sed -i 操作建议先备份原文件
8. 统一 generate_report() 函数到公共库

---

## 六、脚本分类统计

| 类别 | 数量 | 脚本 |
|------|------|------|
| 核心入口 | 1 | devkit.sh |
| 库文件 | 1 | lib_manifest.sh |
| 安装/转换 | 4 | install_assets, convert_assets, sync_codex_assets, catalog_assets |
| 检查/验证 | 6 | validate_assets, check_format, check_change_governance, check_profile_coherence, check-terminology-consistency, quality-gate-check |
| 工作流/发布 | 3 | workflow, release-manager, version-manager |
| 运维监控 | 5 | health-check, monitoring, auto-ops, backup-rollback, performance |
| 安全/桥接 | 3 | security, openspec_bridge, evidence_index |
| 匹配 | 1 | skill_match |
