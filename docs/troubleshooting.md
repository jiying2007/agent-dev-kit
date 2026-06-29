# 故障排除指南

## 概述

本指南帮助你诊断和解决使用 agent-dev-kit 时遇到的常见问题。

## 常见问题

### 1. 安装问题

#### 问题：验证失败
```
[FAIL] validation failed
```

**可能原因**：
- 文件格式错误
- 缺少必需文件
- 配置不正确

**解决方案**：
```bash
# 1. 运行详细验证
bash scripts/validate-assets.sh --strict

# 2. 检查格式
bash scripts/check-format.sh

# 3. 检查必需文件
ls -la manifest.yaml CONTEXT.md README.md
```

#### 问题：GitHub Actions 报 `command not found`
```
scripts/<name>.sh: line N: rtk: command not found
```

**可能原因**：
- active scripts 误依赖本机 Codex 包装命令
- 本地环境 PATH 比 GitHub runner 更宽，掩盖了依赖缺失
- workflow 未安装脚本所需的显式依赖

**解决方案**：
```bash
# 1. 查 active scripts 是否引用本机专属命令
rg -n '(^|[;&|({[:space:]])rtk[[:space:]]+' scripts tests .github

# 2. 用普通 runner 视角复现
PATH=/usr/bin:/bin bash scripts/validate-assets.sh --strict
PATH=/usr/bin:/bin bash scripts/check-format.sh
PATH=/usr/bin:/bin bash tests/run_all.sh
```

ADK 脚本和 CI 不应直接调用 `rtk`；在本机 Codex 会话中执行这些命令时，才由操作者在命令最前面加 `rtk`。

### 2. 测试问题

#### 问题：测试失败
```
All tests passed -> Some tests failed
```

**可能原因**：
- 代码错误
- 配置变更
- 环境问题

**解决方案**：
```bash
# 1. 运行单个测试
bash tests/test_workflow.sh

# 2. 查看详细输出
bash scripts/devkit.sh test --verbose

# 3. 检查测试文件
ls -la tests/
```

### 3. 质量门禁问题

#### 问题：质量门禁失败
```
[FAIL] quality gate check failed
```

**可能原因**：
- 产物不完整
- 配置不一致
- 缺少验证证据

**解决方案**：
```bash
# 1. 运行质量门禁检查
bash scripts/quality-gate-check.sh check-all

# 2. 检查产物完整性
bash scripts/quality-gate-check.sh check-artifacts

# 3. 检查一致性
bash scripts/quality-gate-check.sh check-coherence
```

### 4. 版本问题

#### 问题：版本锁定失败
```
[ERROR] 版本已锁定
```

**可能原因**：
- 版本已锁定
- 权限问题

**解决方案**：
```bash
# 1. 查看当前版本
bash scripts/version-manager.sh current

# 2. 解锁版本
bash scripts/version-manager.sh unlock

# 3. 强制升级到下一目标版本
bash scripts/version-manager.sh upgrade --target 3.0.0 --force
```

### 5. 备份问题

#### 问题：备份失败
```
[ERROR] 目标目录不存在
```

**可能原因**：
- 目录不存在
- 权限问题

**解决方案**：
```bash
# 1. 检查声明式资产仓库
ls -la /tmp/adk-runtime

# 2. 创建目录
mkdir -p /tmp/adk-runtime

# 3. 重新备份
bash scripts/backup-rollback.sh backup --target /tmp/adk-runtime
```

### 6. 健康检查问题

#### 问题：健康检查失败
```
[ERROR] 健康检查失败
```

**可能原因**：
- 目录结构不完整
- 依赖缺失
- 配置错误

**解决方案**：
```bash
# 1. 运行详细健康检查
bash scripts/health-check.sh check-all --verbose

# 2. 检查目录结构
bash scripts/health-check.sh check-structure --verbose

# 3. 检查依赖
bash scripts/health-check.sh check-dependencies --verbose
```

## 诊断步骤

### 1. 收集信息

```bash
# 系统信息
uname -a

# Bash版本
bash --version

# Git版本
git --version

# 磁盘空间
df -h .

# 文件权限
ls -la
```

### 2. 检查环境

```bash
# 检查环境变量
env | grep -E "PATH|HOME|SHELL"

# 检查当前目录
pwd

# 检查文件列表
ls -la
```

### 3. 运行诊断

```bash
# 运行所有检查
bash scripts/health-check.sh check-all --verbose

# 运行测试
bash tests/run_all.sh

# 运行质量门禁
bash scripts/quality-gate-check.sh check-all
```

## 获取帮助

### 1. 查看文档

- 使用指南: `docs/usage.md`
- 命令参考: `docs/commands.md`
- 最佳实践: `docs/best-practices.md`

### 2. 检查日志

```bash
# 查看系统日志
tail -f /var/log/syslog

# 查看应用日志
tail -f /tmp/adk-runtime/logs/*.log
```

### 3. 提交问题

如果问题无法解决，请提交问题：

1. 收集错误信息
2. 记录重现步骤
3. 提供系统信息
4. 提交到问题跟踪系统

## 预防措施

### 1. 定期备份

```bash
# 创建定期备份
bash scripts/backup-rollback.sh backup --target /tmp/adk-runtime
```

### 2. 定期检查

```bash
# 定期运行健康检查
bash scripts/health-check.sh check-all
```

### 3. 版本管理

```bash
# 锁定当前稳定版本
bash scripts/version-manager.sh lock --version 2.9.0
```

### 4. 测试验证

```bash
# 定期运行测试
bash tests/run_all.sh
```

## 常见错误代码

| 错误代码 | 描述 | 解决方案 |
|---------|------|---------|
| 1 | 一般错误 | 检查命令语法 |
| 2 | 权限错误 | 检查文件权限 |
| 126 | 权限不足 | 使用chmod +x |
| 127 | 命令未找到 | 检查PATH |
| 130 | 用户中断 | 重新运行 |

## 最佳实践

### 1. 定期维护

- 每周运行健康检查
- 每月创建备份
- 定期更新文档

### 2. 监控告警

- 设置健康检查定时任务
- 监控磁盘空间
- 监控错误日志

### 3. 版本控制

- 使用版本锁定
- 记录变更日志
- 定期发布版本

---

**提示**：遇到问题时，先运行健康检查，再查看故障排除指南。
