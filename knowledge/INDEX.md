# 知识目录索引

> 最后更新: 2026-05-12
> 知识总数: 6

## 按层级索引

### L0-toolchain (工具链配置知识)

| 文件 | 描述 | 成熟度 |
|------|------|--------|
| codex-config.md | Codex 配置指南 | verified |

### L1-general-tech (通用技术知识)

| 文件 | 描述 | 成熟度 |
|------|------|--------|
| coding-standards.md | 编码规范 | verified |

### L2-domain (业务领域知识)

| 文件 | 描述 | 成熟度 |
|------|------|--------|
| embedded-patterns.md | 嵌入式开发模式 | verified |

### L3-project (项目上下文)

| 文件 | 描述 | 成熟度 |
|------|------|--------|
| architecture-decisions/adr-001-8-phase-lifecycle.md | 8 阶段生命周期决策 | accepted |
| historical-decisions/why-knowledge-layer.md | 知识分层架构决策 | accepted |

### L4-session (会话上下文)

| 文件 | 描述 | 成熟度 |
|------|------|--------|
| (当前无内容) | - | - |

## 按类型索引

### 规则型 (Rules)

| 文件 | 层级 | 成熟度 |
|------|------|--------|
| coding-standards.md | L1 | verified |

### 模式型 (Patterns)

| 文件 | 层级 | 成熟度 |
|------|------|--------|
| embedded-patterns.md | L2 | verified |

### 案例型 (Cases)

| 文件 | 层级 | 成熟度 |
|------|------|--------|
| (当前无内容) | - | - |

### 经验型 (Experiences)

| 文件 | 层级 | 成熟度 |
|------|------|--------|
| (当前无内容) | - | - |

### 索引型 (Indexes)

| 文件 | 层级 | 成熟度 |
|------|------|--------|
| (当前无内容) | - | - |

## 按成熟度索引

### Draft (草稿)

| 文件 | 层级 | 类型 |
|------|------|------|
| (当前无内容) | - | - |

### Verified (验证)

| 文件 | 层级 | 类型 |
|------|------|------|
| codex-config.md | L0 | - |
| coding-standards.md | L1 | rules |
| embedded-patterns.md | L2 | patterns |

### Mature (成熟)

| 文件 | 层级 | 类型 |
|------|------|--------|
| (当前无内容) | - | - |

## 搜索指南

### 按关键词搜索

```bash
# 搜索包含 "嵌入式" 的知识
grep -r "嵌入式" knowledge/

# 搜索包含 "状态机" 的知识
grep -r "状态机" knowledge/
```

### 按层级搜索

```bash
# 列出 L2 层级的所有知识
ls knowledge/L2-domain/
```

### 按成熟度搜索

```bash
# 列出所有 verified 的知识
grep -r "maturity: verified" knowledge/
```

## 维护指南

### 添加新知识

1. 确定知识层级（L0-L4）
2. 确定知识类型（rules/patterns/cases/experiences/indexes）
3. 创建知识文件
4. 更新本索引

### 更新成熟度

1. 验证知识内容
2. 更新 maturity 字段
3. 更新本索引

### 删除过期知识

1. 确认知识不再需要
2. 删除知识文件
3. 更新本索引

## 参考

- 知识分层架构文档: `docs/workflows/knowledge-layer.md`
- 分析报告: `docs/analysis/tencent-article-analysis-20260512.md`
