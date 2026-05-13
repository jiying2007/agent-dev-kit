# flow-kit 全量分析与 adk 完整落地

**来源**: flow-kit 项目
**分析日期**: 2026-05-12
**分析方法**: 全量文件读取 + 模式提取 + adk 对比

---

## 一、flow-kit 架构全景

### 1.1 文件体系

```
flow-kit/
├── GO.md                    # 统一入口 + 路由 + Token 预算
├── SYSTEM.md                # 永久注入版（全局规则）
├── RULES.md                 # 系统级硬规则（R1-R8）
├── METHODOLOGY.md           # 方法论骨架
├── README.md                # 项目说明
├── 阶段 prompt 目录                 # 阶段 prompt（0-7 + 横向命令）
│   ├── 0-change.md
│   ├── 1-requirement.md
│   ├── 2-design.md
│   ├── 2a-ui-design.md
│   ├── 3-task.md
│   ├── 4-dev.md
│   ├── 5-test.md
│   ├── 6-review.md
│   ├── 7-integration.md
│   ├── A-architect.md       # 架构文档
│   ├── A-evolve.md          # 架构沉淀
│   ├── I-intel-scan.md      # 项目扫描
│   ├── L-restyle.md         # 视觉改造
│   └── M-health.md          # 健康检查
├── templates/               # 工件模板
│   ├── CHANGE.md
│   ├── REQUIREMENT.md
│   ├── DESIGN.md
│   ├── UI-DESIGN.md
│   ├── TASK.md
│   ├── SUMMARY.md
│   ├── PROGRESS.md          # 清窗模板（关键）
│   ├── LESSONS.md           # 失败知识库（关键）
│   ├── CONTEXT.md           # 项目上下文
│   ├── ARCHITECTURE.md      # 架构文档
│   ├── STATE.md             # 跨会话状态（关键）
│   ├── REVIEW.md
│   └── TEST.md
└── reference/               # 参考文档
    ├── tech-stacks.md
    ├── test-pyramid.md
    ├── ui-aesthetics.md
    └── ui-anti-patterns.md
```

### 1.2 核心流程

```
CHANGE → REQUIREMENT → DESIGN → [2a UI-DESIGN]* → TASK → DEV → TEST → REVIEW → INTEGRATION → ARCHIVE

* 仅前端项目走 2a；后端/CLI/lib 跳过
```

**MVP 路径**: `REQUIREMENT → TASK → DEV`（3 步，3 文件）

---

## 二、10 大核心机制深度分析

### 2.1 清窗机制 (PROGRESS.md)

**触发信号** (R1.1):
1. 输入 token > 50k
2. AI 复读已说过的内容
3. 同类错误连续 ≥ 2 次
4. 用户感觉对话打转

**清窗前必须完成** (R1.5):
1. 写 PROGRESS.md（已完成/当前/已排除方案/待确认假设）
2. 更新 STATE.md 中断任务字段
3. 输出重启指令给用户

**清窗后恢复顺序** (R1.5):
```
METHODOLOGY → RULES → 当前阶段 prompt → CONTEXT → REQUIREMENT
→ DESIGN（≥阶段2时）→ TASK（≥阶段3时）→ PROGRESS（中途断的）
```

**反重复检查** (R1.6):
1. 读 PROGRESS.md「已排除方案」段
2. 确认下一步不在该清单里
3. 撞了必须先回答"本次与上次的差异是 X"
4. 说不出来就不许动手

**任务过大早期信号** (R1.7):
- 半路触发清窗 = task 拆得不够细
- 恢复后第一动作是就地拆为 ≥ 2 个子任务

**adk 差距**: 完全缺失

### 2.2 失败知识库 (LESSONS.md)

**条目格式**:
```markdown
### L-NNN · [tag1, tag2] 标题

- **首发**: <change-id> · <task-id> · <YYYY-MM-DD>
- **上次复核**: <YYYY-MM-DD>
- **适用栈**: <技术栈>
- **状态**: active / superseded-by:L-MMM / deprecated
- **关键词**: <空格分隔>

**问题场景**
**当时尝试的方案**
**为什么不行**
**当前推荐做法**
**何时可重新评估**
```

**标签索引**:
- `arch` 架构决策类
- `lib` 第三方库选型/陷阱
- `tool` 构建/测试/工具链
- `data` 数据建模/迁移
- `perf` 性能
- `sec` 安全
- `ux` 交互/视觉
- `ops` 部署/运维
- `proc` 流程/协作

**提名条件** (满足任一即入库):
- 调试/试错总耗时 > 30 分钟
- 错因不局限于本任务，其它任务也会撞上
- 未来 6 个月内有合理概率被再次尝试
- 否决理由不写在 ADR 里就会丢失

**反例** (不进 LESSONS):
- 一次性拼写错误
- 项目独有的业务规则（应进 CONTEXT.md）
- 已在 ADR 中详细说明的架构权衡

**使用方式** (R1.8):
1. DEV 任务进入实现前 grep LESSONS.md
2. 命中条目必须显式声明"差异是 X"或"仍适用所以不重试"
3. INTEGRATION ARCHIVE 前按提名条件扫描入库

**adk 差距**: 有框架但缺自动沉淀机制

### 2.3 三层架构分层

| 层级 | 文件 | 内容 | 加载频率 |
|------|------|------|----------|
| Rules 层 | CONTEXT.md | 技术栈、命名约定、禁动清单 | 每个 change |
| Structure 层 | ARCHITECTURE.md | 模块图、ADR、扩展点 | 仅 design/evolve |
| Change 层 | DESIGN.md | 单次 change 技术决策 | 归档后冻结 |

**边界清晰**: CONTEXT 回答"AI 写代码时该遵守什么"，ARCHITECTURE 回答"系统是怎么搭起来的"，DESIGN 回答"这次 change 怎么做"。

**adk 现状**: 已实现类似架构

### 2.4 STATE.md 跨会话状态

```markdown
## 当前位置
- **活跃 Change**: <change-id>
- **当前阶段**: CHANGE / REQUIREMENT / DESIGN / ...
- **当前 Task**: <T03>
- **中断任务**: <task-id> 或 "无"

## 阻塞与待决策
| 项 | 类型 | 详情 | 待谁 | 自 |

## 决策日志（最近 10 条）
## 已归档 Changes（最近 5 个）
## 横向命令状态
```

**adk 差距**: 有 state.json 但缺 STATE.md 的丰富结构

### 2.5 硬规则 (RULES.md)

**R1 上下文与 Token**:
- R1.1 清窗触发信号
- R1.2 阶段切换输出工件
- R1.3 引用历史用 @文件路径
- R1.4 不允许"我记得"
- R1.5 重启协议
- R1.6 反重复检查
- R1.7 任务过大信号
- R1.8 跨任务失败检查
- R1.9 工件加载预算

**R2 阶段门**:
- R2.1 没 CHANGE 不能进 REQUIREMENT
- R2.2 没 REQUIREMENT 不能进 DESIGN
- R2.3 没 TASK 不能写代码
- R2.4 verify 未通过禁止标记完成
- R2.5 REVIEW Critical 项必须修复
- R2.6 UAT 失败自动重试 ≤ 3 轮

**R3 角色红线**:
- Architect 不写实现代码
- Dev 不改 REQUIREMENT/DESIGN
- Reviewer 不修代码
- 同会话同时间只扮演一个角色

**R4 提交与产物**:
- R4.1 每任务一次原子提交
- R4.2 代码改动必须伴随测试改动
- R4.3 Bug 修复必须伴随回归测试
- R4.4 不能声称"完成"而没跑过 verify

**R5 测试纪律**:
- R5.1 测试用例从 AC 派生
- R5.2 禁止用 mock 屏蔽真实失败
- R5.3 禁止删除/弱化测试来"修复"失败

**R6 反幻觉**:
- R6.1 引用外部 API 前必须 grep 验证
- R6.2 不确定的事实必须明示"待确认"
- R6.3 不能假设代码"应该可以工作"

**R7 范围控制**:
- R7.1 严禁悄悄扩大范围
- R7.2 同次提交不允许混入多个无关任务

**adk 差距**: 有 rules/ 目录但缺这些具体规则

### 2.6 Token 预算管理

**Token 成本表**:

| 阶段 | 完整模式 | 极简模式 | 单点调用 |
|------|----------|----------|----------|
| 规划链 (0-3) | ~42k-62k | ~30k-45k | 按需 |
| 实施 (4×5) | ~125k-300k | ~125k-300k | 单 task ~25k-60k |
| 测试 (5) | ~30k-80k | ~20k-50k | 单独 ~30k |
| Review (6) | ~25k-50k | ~15k-25k | 单独 ~25k |
| 集成 (7) | ~20k-40k | ~15k-25k | 单独 ~20k |
| **总计** | **~250k-530k** | **~205k-445k** | **选什么跑什么** |

**影响因子**:
- 前端项目 +20%
- 涉及 schema 变更 +5-10%
- brooks-lint 已装 +10%
- 跨模型 spot-check +30%
- task 数 < 3 -30%
- task 数 > 10 +50%

**adk 差距**: 完全缺失

### 2.7 工件加载预算 (R1.9)

| 类型 | 路径 | 长度 | 加载方式 |
|------|------|------|----------|
| SPEC | `.specs/<id>/*.md` | < 200 行 | 整读 OK |
| REFERENCE | `reference/*.md` | 75-470 行 | **禁止默认整读** |
| TEMPLATE/PROMPT | `templates/*.md` | < 150 行 | 整读 OK |

**规则**:
1. 首轮预算：reference 总行数 ≤ 150 行
2. 严禁默认整读大型 reference
3. 必须列出每个加载项的起止行
4. 未加载的标在「未加载」段

**adk 差距**: 完全缺失

### 2.8 M-health 健康检查

**功能**:
- 代码库体检
- 扫描重复代码块 (jscpd)
- 扫描未使用导出 (knip)
- 扫描未使用依赖 (vulture)
- 生成健康分
- 严重的直接开修复任务
- 中等的记进技术债清单

**adk 差距**: 有 knowledge-health-check.sh 但缺代码质量检查

### 2.9 A-evolve 架构沉淀

**功能**:
- 从 DESIGN.md 提取"架构沉淀建议"
- 攒几个 change 后运行
- AI 把沉淀拎出来让用户挑
- 用户批准的才写进 CONTEXT 和 ARCHITECTURE
- **AI 不能自己偷偷改项目级文档**

**adk 差距**: 完全缺失

### 2.10 删代码门槛

**规则**:
- 删 ≥ 5 行代码或改公共 API 前
- 先 grep 全库列出所有调用点
- 用户说删才能删
- 因为动态 import、反射、mock 这些 AI 看不到

**adk 差距**: 完全缺失

---

## 三、adk 全量落地计划

### Phase 1: 清窗机制 + STATE.md

**新增文件**:
- `templates/PROGRESS.md` — 清窗模板
- `templates/STATE.md` — 跨会话状态模板
- `knowledge/L4-session/progress.md` — 清窗快照

**修改文件**:
- `AGENTS.md` — 增加清窗规则 (R1.1-R1.7)
- `rules/00-global.md` — 增加上下文规则

### Phase 2: 失败知识库

**新增文件**:
- `knowledge/L2-domain/lessons.md` — 失败知识库模板
- `templates/LESSONS.md` — 失败知识库模板

**修改文件**:
- `AGENTS.md` — 增加 R1.8 跨任务失败检查
- `docs/workflows/lifecycle.md` — 增加 ARCHIVE 阶段知识沉淀

### Phase 3: 硬规则

**新增文件**:
- `rules/coding/03-code-deletion.md` — 删代码门槛
- `rules/coding/04-database-migration.md` — 数据库迁移规则
- `rules/workflow/03-context-budget.md` — Token 预算管理

**修改文件**:
- `rules/00-global.md` — 增加 R2-R7 规则

### Phase 4: 辅助命令

**新增文件**:
- `scripts/code-health-check.sh` — M-health 代码质量检查
- `scripts/architecture-evolve.sh` — A-evolve 架构沉淀

**修改文件**:
- `manifest.yaml` — 增加新脚本

### Phase 5: 验证与提交

- 运行测试
- 更新版本号
- 提交所有变更

---

## 四、与现有 adk 架构的整合

### 4.1 与 8 阶段生命周期整合

```
Spark → Design → Tasks → Build → Review → Test → Ship → Reflect
  ↓        ↓        ↓       ↓        ↓       ↓      ↓        ↓
清窗检查  设计检查  任务检查  实现检查  审查检查  测试检查  发布检查  复盘检查
```

### 4.2 与知识分层架构整合

```
knowledge/
├── L0-toolchain/        # 工具链配置
├── L1-general-tech/     # 通用技术
├── L2-domain/           # 业务领域
│   └── lessons.md       # 失败知识库（新增）
├── L3-project/          # 项目上下文
│   └── architecture.md  # 架构文档（新增）
└── L4-session/          # 会话上下文
    └── progress.md      # 清窗快照（新增）
```

### 4.3 与 Gate 机制整合

```
Gate 检查
    ↓
清窗检查 + 失败知识库检查 + Token 预算检查
    ↓
通过/不通过
```

---

## 五、预期收益

| 收益 | 描述 | 量化指标 |
|------|------|----------|
| **防止 AI 打转** | 清窗机制自动触发 | 清窗触发次数 |
| **防止重复踩坑** | 失败知识库自动 grep | 命中次数 |
| **防止 AI 误删** | 删代码门槛 | 拦截次数 |
| **控制 Token 成本** | 预算管理 | Token 使用量 |
| **知识自动沉淀** | A-evolve 机制 | 沉淀条目数 |

---

## 六、总结

flow-kit 是一个成熟的 AI 编程规范化框架，其核心价值在于：

1. **清窗机制**: 解决 AI 对话打转问题（R1.1-R1.7）
2. **失败知识库**: 解决同样坑反复踩问题（R1.8）
3. **三层架构分层**: 解决知识组织问题
4. **硬规则体系**: 解决 AI 幻觉和范围控制问题（R2-R7）
5. **Token 预算管理**: 解决成本控制问题
6. **删代码门槛**: 解决 AI 误删问题

这些机制与我们 adk 的 8 阶段生命周期和知识分层架构高度互补，可以进一步增强 adk 的防错和知识沉淀能力。

**核心洞察**: flow-kit 的"清窗机制"和"失败知识库"是我们 adk 最需要补强的部分，其次是"硬规则体系"和"Token 预算管理"。
