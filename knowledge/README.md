# 知识分层架构

> 来源: 腾讯技术工程文章《Harness不是目的，知识才是护城河》
> 实施日期: 2026-05-12

## 目录结构

```
knowledge/
├── L0-toolchain/            # Layer 0: 工具链配置知识
├── L1-general-tech/         # Layer 1: 通用技术知识
├── L2-domain/               # Layer 2: 业务领域知识
├── L3-project/              # Layer 3: 项目上下文
│   ├── architecture-decisions/
│   ├── design-patterns/
│   └── historical-decisions/
└── L4-session/              # Layer 4: 会话上下文（临时）
```

## 使用指南

### 查询知识

```bash
# 按层级查询
adk knowledge query --layer L1

# 按类型查询
adk knowledge query --type patterns

# 按成熟度查询
adk knowledge query --maturity mature
```

### 沉淀知识

```bash
# 沉淀知识
adk knowledge add --layer L2 --type experiences --content "踩坑记录"

# 更新成熟度
adk knowledge update --id <id> --maturity verified
```

## 参考

- 知识分层架构文档: `docs/workflows/knowledge-layer.md`
- 分析报告: `docs/analysis/tencent-article-analysis-20260512.md`
