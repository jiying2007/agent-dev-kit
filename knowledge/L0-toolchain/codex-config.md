# Codex 配置指南

> 成熟度: verified
> 最后更新: 2026-05-12

## 概述

本文档记录 Codex CLI 的配置和使用最佳实践。

## 配置目录

```
~/.codex/
├── config.yaml          # 主配置文件
├── auth/                # 认证文件
├── skills/              # 技能目录
└── profiles/            # 配置文件
```

## 常用配置

### 模型配置

```yaml
model: gpt-5.5
provider: openai
```

### 认证配置

```bash
# 登录
codex auth login

# 查看认证状态
codex auth status
```

## 最佳实践

1. 使用 AGENTS.md 定义项目规范
2. 使用 skills/ 目录组织可复用技能
3. 使用 profiles/ 管理不同场景配置

## 参考

- Codex 官方文档
- agent-dev-kit 集成指南
