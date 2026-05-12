# flow-kit 深度分析与 adk 借鉴

**来源**: [开源，开源，融合多个AI工具的AI规范化编程项目发布了！！](https://mp.weixin.qq.com/s/TKSFcvhBSqugYCOTMEoFrQ)
**项目**: github.com/rihebty/flow-kit
**日期**: 2026-05-12

---

## 一、flow-kit 架构概览

flow-kit 是一个融合多个 AI 工具的规范化编程框架，核心理念：

> **AI 会犯错，框架要防错。**

### 核心文件结构

```
flow-kit/
├── GO.md              # 入口，加一句话触发命令
├── RULES.md           # 硬规则（不可违反）
├── CONTEXT.md         # 项目级规则（技术栈、命名、禁用）
├── ARCHITECTURE.md    # 架构级知识（模块图、ADR）
├── DESIGN.md          # 单次变更设计
├── PROGRESS.md        # 清窗时的进度快照
├── LESSONS.md         # 失败知识库
└── changes/           # 变更目录
    └── <change-id>/
        ├── DESIGN.md
        ├── tasks.md
        └── evidence/
```

### 8 步主流程

```
0. 接收需求
1. 拆解任务
2. 设计方案
3. 编码实现
4. 自测验证
5. 代码审查
6. 集成测试
7. 归档沉淀
```

---

## 二、六大核心机制深度分析

### 2.1 清窗机制（PROGRESS.md）

**问题**: AI 对话长了会打转，重走失败的路。

**flow-kit 方案**:

```markdown
# PROGRESS.md

## 当前状态
- 任务: 实现用户登录
- 阶段: 编码实现
- 进度: 60%

## 已排除方案
1. 方案A: 直接用 bcrypt → 失败原因: 依赖安装失败
2. 方案B: 用 argon2 → 失败原因: 性能不达标

## 下一步
- 尝试方案C: 使用 scrypt
```

**核心规则**:
- 清窗前必须写 PROGRESS.md
- 新会话恢复后第一件事读"已排除方案"
- 如果要试的路跟已排除的一样，得先解释"这次有什么不同"
- 说不出来就不许动手

**adk 差距**: 我们有 `knowledge/L4-session/` 但没有清窗机制。

**借鉴价值**: ⭐⭐⭐⭐⭐

### 2.2 失败知识库（LESSONS.md）

**问题**: 同样的坑反复踩。

**flow-kit 方案**:

```markdown
# LESSONS.md

## Prisma 迁移文件
- 踩坑次数: 3
- 最近一次: 2026-05-01
- 教训: 改 schema 必须同时写 migration
- 触发关键词: prisma, schema, model, migration

## Redis 连接池
- 踩坑次数: 2
- 最近一次: 2026-04-28
- 教训: 连接池大小要根据并发量调整
- 触发关键词: redis, connection, pool, timeout
```

**核心规则**:
- 每次 change 归档时，AI 提名有代表性的坑
- 每个任务开工前，AI 用关键词 grep 这个文件
- 命中了就在计划里写清楚"看过了，这次怎么避"

**adk 差距**: 我们有 `knowledge/L2-domain/` 但没有自动沉淀机制。

**借鉴价值**: ⭐⭐⭐⭐⭐

### 2.3 架构知识三层分层

**问题**: 架构决策分散在各自的 DESIGN.md 里，半年后没人翻。

**flow-kit 方案**:

| 层级 | 文件 | 内容 | 更新频率 |
|------|------|------|----------|
| L1 | CONTEXT.md | 规则（技术栈、命名、禁用） | 低 |
| L2 | ARCHITECTURE.md | 结构（模块图、ADR） | 中 |
| L3 | DESIGN.md | 单次变更 | 每次 change |

**沉淀流程**:
1. 每个 DESIGN.md 有"架构沉淀建议"段
2. 攒几个 change 后跑 `A-evolve`
3. AI 把沉淀拎出来让你挑
4. 你批准的才写进 CONTEXT 和 ARCHITECTURE
5. **AI 不能自己偷偷改项目级文档**

**adk 现状**: 我们已实现类似架构：
- `CONTEXT.md` = CONTEXT.md
- `knowledge/L3-project/` = ARCHITECTURE.md
- `docs/changes/` = DESIGN.md

**借鉴价值**: ⭐⭐⭐（已实现）

### 2.4 辅助命令

| 命令 | 功能 | 实现方式 |
|------|------|----------|
| `M-health` | 代码库体检 | jscpd/knip/vulture + grep 兜底 |
| `L-restyle` | 视觉风格改造 | 识别调性 → 选新风格 → 改造计划 |
| `A-architect` | 架构文档 | 首次建或大重构 |
| `A-evolve` | 架构沉淀 | 从 DESIGN.md 提取 → 批准 → 写入 |

**adk 现状**: 我们有 `knowledge-health-check.sh` 但没有 M-health 的代码质量检查。

**借鉴价值**: ⭐⭐⭐⭐

### 2.5 两条硬规则

#### 规则 1: 改数据库 schema 必须同一个 commit 里带迁移文件

```markdown
# RULES.md

## 数据库变更规则
- 改 schema 必须同一个 commit 里带迁移文件
- AI 很爱只改 model 不写 migration
- 本地能跑但生产必炸
```

#### 规则 2: 删代码有门槛

```markdown
# RULES.md

## 代码删除规则
- 删 ≥ 5 行代码或改公共 API 前
- 先 grep 全库列出所有调用点
- 你说删才能删
- 因为动态 import、反射、mock 这些 AI 看不到
```

**adk 差距**: 我们有 `rules/` 目录但没有这两条具体规则。

**借鉴价值**: ⭐⭐⭐⭐⭐

### 2.6 MVP 模式

**问题**: 8 步全走对小东西来说太重了。

**flow-kit 方案**:

```
完整模式: 0-1-2-3-4-5-6-7 (8步)
MVP模式: 0-1-3 (3步)

产物:
- 完整模式: PROGRESS.md + DESIGN.md + tasks.md + evidence/
- MVP模式: requirements.md + tasks.md + code
```

**adk 现状**: 我们有"快速模式"（Spark → Tasks → Build → Ship）。

**借鉴价值**: ⭐⭐（已实现）

---

## 三、flow-kit vs adk 对比

| 维度 | flow-kit | adk | 差距 |
|------|----------|-----|------|
| **清窗机制** | PROGRESS.md + 已排除方案 | 无 | **需补强** |
| **失败知识库** | LESSONS.md + 自动 grep | knowledge/L2/ 框架 | **需补强** |
| **架构分层** | CONTEXT/ARCHITECTURE/DESIGN | CONTEXT.md + knowledge/ | 已实现 |
| **健康检查** | M-health | knowledge-health-check.sh | 已实现 |
| **硬规则** | RULES.md (删代码门槛) | rules/ 框架 | **需补强** |
| **MVP 模式** | 3 步简化流程 | 快速模式 | 已实现 |
| **架构沉淀** | A-evolve 批准机制 | 无 | **需补强** |
| **生命周期** | 8 步主流程 | 8 阶段生命周期 | 已实现 |

---

## 四、可立即吸收的 P0 模式

### 4.1 清窗机制

**落地方式**:

```bash
# 在 knowledge/L4-session/ 下创建清窗模板
knowledge/L4-session/
├── progress.md          # 清窗时的进度快照
└── excluded-approaches.md  # 已排除方案
```

**在 AGENTS.md 中增加规则**:

```markdown
## 清窗规则

当对话超过 50 轮或 AI 开始打转时：
1. 必须先写 progress.md（当前状态 + 已排除方案）
2. 新会话恢复后第一件事读"已排除方案"
3. 如果要试的路跟已排除的一样，得先解释"这次有什么不同"
4. 说不出来就不许动手
```

### 4.2 失败知识库

**落地方式**:

```bash
# 在 knowledge/L2-domain/ 下创建失败知识库
knowledge/L2-domain/
└── lessons.md           # 失败知识库
```

**格式**:

```markdown
# 失败知识库

## I2C 总线仲裁失败
- 踩坑次数: 3
- 最近一次: 2026-05-01
- 教训: 多主机场景必须处理仲裁失败中断
- 触发关键词: i2c, arbitration, multi-master

## SPI 时钟极性配置错误
- 踩坑次数: 2
- 最近一次: 2026-04-28
- 教训: CPOL/CPHA 必须与从设备一致
- 触发关键词: spi, cpol, cpha, clock
```

### 4.3 删代码门槛规则

**落地方式**:

```bash
# 在 rules/coding/ 下增加规则
rules/coding/
└── 03-code-deletion.md  # 代码删除规则
```

**内容**:

```markdown
## 代码删除规则

- 删 ≥ 5 行代码或改公共 API 前
- 先 grep 全库列出所有调用点
- 你说删才能删
- 因为动态 import、反射、mock 这些 AI 看不到
```

---

## 五、实施计划

### Phase 1: 立即执行（本周）

1. ✅ 创建清窗机制模板
2. ✅ 创建失败知识库
3. ✅ 增加删代码门槛规则

### Phase 2: 中期落地（下周）

1. ⬜ 实现 A-evolve 架构沉淀命令
2. ⬜ 实现 M-health 代码质量检查
3. ⬜ 在生命周期中集成清窗机制

### Phase 3: 长期演进（1 个月内）

1. ⬜ 实现失败知识库自动 grep
2. ⬜ 实现架构沉淀自动提取
3. ⬜ 实现清窗自动触发

---

## 六、总结

flow-kit 的核心价值在于：

1. **清窗机制**: 解决 AI 对话打转问题
2. **失败知识库**: 解决同样坑反复踩问题
3. **架构沉淀**: 解解决策分散问题
4. **删代码门槛**: 解决 AI 误删问题

这些机制与我们 adk 的知识分层架构高度互补，可以进一步增强 adk 的知识沉淀和防错能力。

**核心洞察**: flow-kit 的"清窗机制"和"失败知识库"是我们 adk 最需要补强的部分。
