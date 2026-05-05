# 快速入门指南

## 概述

本指南帮助你快速上手 global-dev-kit（gdk），了解其核心概念和基本使用方法。

## 前置条件

- Bash 4.0+
- Git
- 基本的命令行操作知识

## 安装

### 1. 克隆仓库

```bash
git clone <repository-url>
cd global-dev-kit
```

### 2. 验证安装

```bash
bash scripts/health-check.sh check-all
```

### 3. 运行测试

```bash
bash tests/run_all.sh
```

## 核心概念

### 1. 产物（Artifacts）
产物是标准化的文档和文件，用于记录开发过程中的各种信息。

### 2. 工作流（Workflows）
工作流是标准化的开发流程，指导如何进行开发活动。

### 3. Profile
Profile 是配置文件，定义了工具的行为和规则。

### 4. 质量门禁（Quality Gates）
质量门禁是检查点，确保开发过程符合质量标准。

## 基本使用

### 1. 创建变更

```bash
bash scripts/workflow.sh propose --change my-feature --title "我的功能"
```

### 2. 推进变更

```bash
bash scripts/workflow.sh advance --change my-feature
```

### 3. 查看状态

```bash
bash scripts/workflow.sh status --change my-feature
```

### 4. 归档变更

```bash
bash scripts/workflow.sh archive --change my-feature
```

## 常见任务

### 1. 检查质量

```bash
bash scripts/quality-gate-check.sh check-all
```

### 2. 创建备份

```bash
bash scripts/backup-rollback.sh backup --target ~/.codex
```

### 3. 查看版本

```bash
bash scripts/version-manager.sh current
```

### 4. 健康检查

```bash
bash scripts/health-check.sh check-all
```

## 下一步

- 阅读 [使用指南](usage.md) 了解更多功能
- 查看 [最佳实践](best-practices.md) 了解使用技巧
- 阅读 [故障排除](troubleshooting.md) 解决常见问题
- 查看 [贡献指南](CONTRIBUTING.md) 了解如何贡献

## 获取帮助

- 查看文档目录 `docs/`
- 运行健康检查 `bash scripts/health-check.sh check-all`
- 查看故障排除指南 `docs/troubleshooting.md`

---

**提示**：建议先运行健康检查，确保环境正常后再开始使用。
