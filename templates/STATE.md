# STATE — 跨会话项目状态

> 仓库根 `STATE.md`。AI 每次开始新会话先读这个，结束前更新。

---

## 当前位置

- **活跃 Feature**: `<feature-name>` 或 "无"
- **当前阶段**: Spark / Design / Tasks / Build / Review / Test / Ship / Reflect / 无
- **当前 Task**: `<task-id>` 或 "—"
- **中断任务**（来自清窗）: `<task-id>` 或 "无"
  - 若非空，下一会话必须先加载 `PROGRESS.md`
- **会话开始建议**:
  - 若有「中断任务」：按清窗后加载顺序恢复
  - 若有活跃 feature：先读相关产物
  - 若无：等用户给新需求

## 阻塞与待决策

| 项 | 类型 | 详情 | 待谁 | 自 |
|---|---|---|---|---|
|  | bug / 决策 / 范围 |  | 用户 |  |

## 决策日志（最近 10 条，倒序）

- `[YYYY-MM-DD]` <一句话决策> — `@docs/changes/<feature>/design.md`

## 已归档 Features（最近 5 个，倒序）

| 日期 | Feature | 摘要 |
|---|---|---|
| YYYY-MM-DD | <feature-name> | <摘要> |

---

## 横向命令状态

```yaml
# 健康巡检
last_health_at: 2026-05-12
last_health_score: 85

# 知识库检查
last_knowledge_check_at: 2026-05-12

# 架构沉淀
last_evolve_at: 2026-05-12
```

---

## 健康检查（AI 每次会话结束前建议运行）

```bash
bash scripts/knowledge-health-check.sh check-all
```
