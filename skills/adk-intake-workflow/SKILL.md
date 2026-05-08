---
name: adk-intake-workflow
description: 子仓接入工作流——扫描、分析、决策与治理覆盖
version: 1.0.0
last_updated: 2026-05-08
triggers:
  - "接入新仓库"
  - "新增子仓"
  - "onboard"
  - "add repo"
  - "纳入治理"
non_triggers:
  - 已接入子仓的日常同步（使用 sync-subrepos.sh）
  - 纯代码阅读或探索
inputs:
  - 仓库 URL 或本地路径、预期定位、优先级
outputs:
  - 仓库分析报告（结构/优点/缺点/adk 借鉴点）
  - 接入决策（adopt / watch / reject）
  - registry.csv 更新、adoption-matrix.md 更新
constraints:
  - 未完成深度分析不得标记为 adopted
  - 优点/缺点必须有具体证据支撑
  - 接入决策必须更新 registry.csv 和 adoption-matrix.md
---

# adk-intake-workflow

## Goal

为新增参考子仓提供标准化的"扫描→分析→决策→治理覆盖"工作流，确保每个接入的仓库都经过结构化评估，避免"盲目纳入"或"遗漏高价值仓库"。

## 来源说明

- **核心来源**：`llm_agent/AGENTS.md` 第 2 节"参考子仓全量清单"与"D1-D2 优点/缺点提炼"
- **意图路由**：`AGENTS.md` 第 1.1 节"接入新仓库"意图
- **治理机制**：`subrepos/registry.csv`（子仓 SSOT）+ `subrepos/adoption-matrix.md`（评估矩阵）
- **分析技能**：`adk-repo-prompt-analyzer`（Prompt 逆向）+ `adk-skill-deep-analyzer`（Skill 深度拆解）
- **脚本入口**：`scripts/new-repo-onboard.sh`（自动化接入）

## 模式描述

### 1. 接入流程总览

```
发现候选 → 初步扫描 → 深度分析 → 优点/缺点提炼 → 接入决策 → 治理覆盖 → 压实验证
```

### 2. 阶段详解

#### Phase 1: 发现候选

候选来源：
- GitHub trending / 话题搜索
- 参考子仓的依赖或关联项目
- 社区推荐或技术文章
- 用户主动提出

```md
[candidate-intake]
source: <发现来源>
repo_url: <url>
expected_role: 方法论 | Agent/Skill | 质量/交付 | 文档/知识 | 配置治理
priority: p0 | p1 | p2
```

#### Phase 2: 初步扫描（5 分钟快筛）

```bash
# 克隆仓库
git clone --depth 1 <repo_url> /tmp/intake-<repo-name>

# 结构快览
tree -L 2 /tmp/intake-<repo-name> -I 'node_modules|.git|__pycache__'

# 关键文件检查
ls /tmp/intake-<repo-name>/{README*,AGENTS*,SKILL*,manifest*,package.json,Makefile,CMakeLists.txt} 2>/dev/null

# 规模评估
find /tmp/intake-<repo-name> -type f | wc -l
```

快筛决策：
- 有价值 → 进入 Phase 3
- 价值不明确 → 标记 watch，暂不纳入
- 明确无关 → reject 并记录原因

#### Phase 3: 深度分析

使用 `adk-repo-prompt-analyzer` + `adk-skill-deep-analyzer` 执行结构化分析：

**3.1 Prompt 逆向（四阶段）**
1. 识别仓库中的指令型文档（AGENTS.md / README / CONTRIBUTING 等）
2. 提取触发词、约束、输出格式
3. 映射到 adk 能力体系
4. 生成 Prompt 资产清单

**3.2 Skill 深度拆解（八阶段）**
1. 目录结构分析
2. 核心文件识别
3. 依赖关系梳理
4. 配置模式提取
5. 测试覆盖评估
6. 文档完整性评估
7. 与 adk 兼容性评估
8. 借鉴价值评估

#### Phase 4: 优点/缺点提炼

```md
## 评估矩阵: <repo-name>

### 优点（可借鉴）
1. <优点描述> — 证据: <具体文件/代码/文档>
2. ...

### 缺点（需摒弃）
1. <缺点描述> — 证据: <具体文件/代码/文档>
2. ...

### adk 借鉴点
1. <可直接迁移的做法>
2. <需要适配后迁移的做法>

### 风险
1. <迁移风险>
2. <维护成本>
```

#### Phase 5: 接入决策

| 决策 | 条件 | 后续动作 |
|------|------|----------|
| **adopt** | 优点明确、可直接借鉴、风险可控 | 更新 registry.csv + adoption-matrix.md |
| **watch** | 有潜力但当前不成熟 | 仅记录到候选池，定期复查 |
| **reject** | 价值低或风险高 | 记录拒绝原因，不再追踪 |

#### Phase 6: 治理覆盖

```bash
# 更新子仓 SSOT
echo "<repo-name>,<repo_url>,<role>,<priority>,adopted,<date>" >> subrepos/registry.csv

# 同步子仓代码
bash scripts/sync-subrepos.sh --repo <repo-name>

# 覆盖校验
bash scripts/check-agents-coverage.sh
```

#### Phase 7: 压实验证

```bash
# 压实就绪检查
bash scripts/check-adk-harden-readiness.sh . --skip-full-suite

# 验证借鉴点已落地
bash scripts/devkit.sh validate --strict
```

### 3. 接入记录模板

```md
# 接入报告: <repo-name>

## 基本信息
- 仓库: <repo_url>
- 定位: <role>
- 优先级: <priority>
- 接入日期: <date>

## 分析结果
### 优点
1. ...

### 缺点
1. ...

### adk 借鉴点
1. ...

## 接入决策: adopt / watch / reject

## 治理覆盖
- [ ] registry.csv 已更新
- [ ] adoption-matrix.md 已更新
- [ ] 子仓代码已同步
- [ ] 覆盖校验已通过
- [ ] 压实验证已通过
```

### 4. 意图路由集成

用户说"接入新仓库"时，AI 自动执行：

```bash
# 1. 加载技能
# 自动加载 adk-intake-workflow

# 2. 执行接入
bash scripts/new-repo-onboard.sh <repo_url>

# 3. 生成报告
# AI 自动生成接入报告
```

## Commands

```bash
# 克隆候选仓库
git clone --depth 1 <repo_url> /tmp/intake-<repo-name>

# 结构扫描
tree -L 2 /tmp/intake-<repo-name> -I 'node_modules|.git'

# 更新 registry
vi subrepos/registry.csv

# 同步子仓
bash scripts/sync-subrepos.sh --repo <repo-name>

# 覆盖校验
bash scripts/check-agents-coverage.sh

# 压实校验
bash scripts/check-adk-harden-readiness.sh . --skip-full-suite
```

## Workflow

1. 扫描候选仓库（GitHub trending / 社区推荐 / 自动发现）
2. 5 分钟快筛（README / LICENSE / 目录结构 / 活跃度）
3. 深度分析（四阶段 Prompt 逆向 + 八阶段 Skill 拆解）
4. 提炼优点/缺点（需有具体证据支撑）
5. 接入决策（adopt / watch / reject）
6. 治理覆盖（更新 registry.csv + adoption-matrix.md）
7. 压实验证（adk 本地验证通过后才标记 adopted）

## Quality Gate

1. 未完成深度分析不得标记为 adopted
2. 优点/缺点必须有具体证据支撑
3. 接入决策必须更新 registry.csv 和 adoption-matrix.md
4. watch 类仓库必须设定复查周期
5. reject 决策必须记录具体原因

## 待完善事项

- [ ] `scripts/new-repo-onboard.sh` 脚本实现（当前为手动流程）
- [ ] 仓库自动发现机制（GitHub API 集成）
- [ ] 分析报告模板标准化（当前各报告格式不统一）
- [ ] 接入决策的自动化程度提升（当前依赖人工判断）
- [ ] 与 `adk-skill-deep-analyzer` 的流程串联（当前为独立执行）
- [ ] 接入后的定期复查机制（watch 类仓库的自动提醒）
