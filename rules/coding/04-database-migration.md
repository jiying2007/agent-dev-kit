---
id: coding-004-database-migration
title: 数据库迁移规则
languages: [sql, python, javascript]
layers: [data]
stages: [build, review]
checks: [migration-included]
---

# 数据库迁移规则

> 来源: flow-kit RULES.md (2026-05-12)

## 规则描述

AI 很爱只改 model 不写 migration，本地能跑但生产必炸。必须在同一个 commit 里包含迁移文件。

## 规则要求

### R9.1 迁移文件必须同步

修改数据库 schema 必须在同一个 commit 里包含：
1. Schema 变更（model 定义）
2. 迁移文件（migration script）
3. 回滚脚本（rollback script）

### R9.2 实现方式

```bash
# 生成迁移文件
alembic revision --autogenerate -m "description"
prisma migrate dev --name description
django makemigrations

# 验证迁移文件存在
ls -la migrations/alembic/versions/
ls -la prisma/migrations/
ls -la app/migrations/
```

### R9.3 迁移文件要求

- 必须有明确的描述
- 必须有回滚脚本
- 必须在测试环境验证
- 必须有数据备份策略

## 示例

### 正确示例

```
commit: feat(auth): add user table
- src/models/user.py (model 定义)
- migrations/001_add_user_table.py (迁移文件)
- migrations/001_add_user_table_rollback.py (回滚脚本)
```

### 错误示例

```
commit: feat(auth): add user table
- src/models/user.py (只有 model，没有 migration)
```

## 检查命令

```bash
# 检查是否有未包含迁移的 schema 变更
git diff --name-only | grep -E "(model|schema)" | while read f; do
    if ! git diff --name-only | grep -q "migration"; then
        echo "WARNING: $f changed but no migration found"
    fi
done
```

## 参考

- flow-kit RULES.md
- AGENTS.md R9 数据库迁移规则
