<!-- repo-intro:start -->
## 仓库介绍（持续维护）

- 仓库名称：`agent-dev-kit`
- 仓库定位：嵌入式系统开发 Agent/Skill 资产与工作流门禁工具包
- 领域范围：BSP/驱动/RTOS/协议栈/硬件调试/交叉编译（不包含前端/后端/云原生）
- 维护状态：持续维护（人工 + Agent 协作）
- 维护目标：在不偏离上游核心定位的前提下，保持中文可读说明、可执行流程与可验证交付。
- 维护边界：默认优先更新文档、规则与配置；涉及大规模重构或行为变更需先评估影响并记录。
- 最小验证：`bash scripts/devkit.sh test`
- 维护记录：建议在每次关键调整后追加"变更摘要 + 验证结果 + 日期"。

<!-- repo-intro:end -->

# Repository Guidelines

## Project Structure & Module Organization
- `agents/`: role-specific agent instructions (`agents/<name>/AGENTS.md`).
- `skills/`: core reusable skills (`skills/<name>/SKILL.md`).
- `optional-skills/`: opt-in skills, only installed/exported when explicitly requested.
- `scripts/`: install/convert/validate/workflow/catalog/match entrypoints.
- `docs/`: usage, commands, workflow guide, runbooks, change artifacts.
- `tests/`: shell-based regression suite and fixtures.
- `manifest.yaml`: single source of truth for tools, profiles, agents, skills, optional skills.

## Build, Test, and Development Commands
- `bash scripts/devkit.sh validate --strict`: full structure/schema validation.
- `bash scripts/devkit.sh validate --quick`: fast pre-check for local iteration.
- `bash scripts/devkit.sh install --tool codex --profile core`: install assets.
- `bash scripts/devkit.sh convert --target claude-code --profile core --out dist --clean`: export assets.
- `bash scripts/devkit.sh catalog build`: regenerate catalog docs.
- `bash scripts/devkit.sh match --skill adk-requirements-triage --text "..."`: trigger matching.
- `bash tests/run_all.sh`: complete regression (required before merge).

## Coding Style & Naming Conventions
- Shell scripts use `bash`, `set -euo pipefail`, LF endings, and kebab-case file names.
- Agent/Skill IDs must be kebab-case and match manifest names.
- `SKILL.md` requires frontmatter keys: `name/description/triggers/non_triggers/inputs/outputs/constraints`.
- Prefer small, focused changes; avoid unrelated refactors.

## Testing Guidelines
- Add or update tests for every behavior change in `scripts/`, `manifest.yaml`, or templates.
- Keep tests deterministic and non-interactive.
- For workflow changes, validate `propose -> apply -> verify -> review -> archive` end-to-end.
- Ensure state transition gates are preserved (`proposed -> applied -> verified -> review-passed`).

## Commit & Pull Request Guidelines
- Commit format: `<type>(scope): <summary>` (e.g., `feat(workflow): 增加 review 门禁`).
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.
- PRs must include: change summary, validation evidence, risk/rollback note, and affected files.

## Safety & Quality Gates
- Do not claim completion without verification evidence.
- Debugging follows read-only-first and single-variable experiments.
- Keep negative findings (`negative-results.md`) to avoid repeated failed paths.
- Breaking changes must be explicitly declared with migration and rollback plans.
- One change should focus on one real problem; avoid bundling unrelated fixes.
- Explicitly decide whether a capability belongs to `core` or `optional-skills`.

## AI 防幻觉与范围控制规则（flow-kit 吸收）

> 来源: flow-kit SYSTEM.md (2026-05-12)

### R1 上下文与清窗规则

- **R1.1 清窗触发信号**: 出现以下任一信号时必须触发清窗：
  1. 输入 token > 50k
  2. AI 复读已说过的内容（自我提示症状）
  3. 同类错误连续出现 ≥ 2 次
  4. 用户感觉对话打转

- **R1.2 阶段切换输出**: 阶段切换时必须输出本阶段工件文件，作为后续唯一上下文来源

- **R1.3 引用历史决策**: 引用历史决策必须用 `@文件路径` 形式，禁止粘贴正文复述

- **R1.4 不允许"我记得"**: 不允许"我记得我们之前说过……"这类对话依赖，所有决策必须可在 `.md` 里查到

- **R1.5 重启协议（清窗前后必须严格执行）**:
  - **清窗前**: ① 写 PROGRESS.md（已完成/当前/已排除方案/待确认假设）② 更新 STATE.md 中断任务字段 ③ 输出重启指令
  - **清窗后**: 按 METHODOLOGY → RULES → 当前阶段 prompt → CONTEXT → REQUIREMENT → DESIGN → TASK → PROGRESS 顺序加载

- **R1.6 反重复检查（清窗恢复后第一件事）**:
  1. 读 PROGRESS.md「已排除方案」段
  2. 确认下一步不在该清单里
  3. 撞了必须先回答"本次与上次的差异是 X"
  4. 说不出来就不许动手

- **R1.7 任务过大早期信号**: 半路触发清窗 = task 拆得不够细，恢复后第一动作是就地拆为 ≥ 2 个子任务

- **R1.8 跨任务失败检查（任何 Build 任务进入实现前必跑）**:
  1. AI 用当前任务的关键词 grep `knowledge/L2-domain/lessons.md`
  2. 命中条目必须显式声明"差异是 X"或"仍适用所以不重试"
  3. Reflect 阶段按提名条件扫描并入库

### R2 阶段门

- **R2.1** 没需求文档不能进 Design
- **R2.2** 没设计文档不能进 Tasks
- **R2.3** 没 tasks.md 不能写代码；每任务必含可执行 verify
- **R2.4** verify 未通过禁止标记完成
- **R2.5** Review 标 Critical 项必须修复或显式接受
- **R2.6** 测试失败自动重试 ≤ 3 轮，超限暂停

### R3 角色红线

- 设计者不写实现代码
- 实现者不改需求/设计文档（发现问题开新 feature）
- 审查者不修代码（只产报告 + 修复 task）
- 同会话同时间只扮演一个角色，切换角色必须清窗

### R4 提交与产物

- **R4.1** 每任务一次原子提交，格式 `<type>(scope): <task-id> <subject>`
- **R4.2** 代码改动必须伴随测试改动
- **R4.3** Bug 修复必须伴随回归测试
- **R4.4** 不能声称"完成"而没跑过 verify

### R5 测试纪律

- **R5.1** 测试用例必须从验收标准派生，禁止从实现派生
- **R5.2** 禁止用 mock 屏蔽真实失败
- **R5.3** 禁止删除/弱化测试来"修复"失败

### R6 反幻觉

- **R6.1** 引用外部 API/字段名前必须 grep 验证存在性
- **R6.2** 不确定的事实必须明示"待确认"，禁止伪装已知
- **R6.3** 不能假设代码"应该可以工作"——必须实际跑 verify

### R7 范围控制

- **R7.1** 严禁悄悄扩大范围；超出 tasks.md 必须先停下更新或开新 feature
- **R7.2** 同次提交不允许混入多个无关任务

### R8 删代码门槛

- **R8.1** 删 ≥ 5 行代码或改公共 API 前，先 grep 全库列出所有调用点
- **R8.2** 用户说删才能删
- **R8.3** 因为动态 import、反射、mock 这些 AI 看不到

## 8 阶段生命周期框架（VibeFlow 吸收）

> 来源: vibeflow 子仓深度分析 (2026-05-12)

### 生命周期定义

```
Spark → Design → Tasks → Build → Review → Test → Ship → Reflect
```

| 阶段 | 目标 | 输入 | 输出 | 门禁 |
|------|------|------|------|------|
| **Spark** | 需求澄清与价值验证 | 用户需求/问题描述 | 需求文档、价值评估 | 需求完整性检查 |
| **Design** | 技术方案设计 | 需求文档 | 设计文档、接口规范 | 三维评审通过 |
| **Tasks** | 合同化任务拆解 | 设计文档 | tasks.md、feature-list.json | 任务边界清晰 |
| **Build** | TDD 驱动开发 | tasks.md | 代码、单元测试 | 测试通过 |
| **Review** | 多视角代码审查 | 代码变更 | 审查报告 | 无阻塞性问题 |
| **Test** | 系统测试与 QA | 代码变更 | 测试报告 | 测试通过 |
| **Ship** | 发布部署 | 测试通过的代码 | 发布产物 | 发布门禁通过 |
| **Reflect** | 复盘沉淀 | 发布产物 | 复盘报告、经验教训 | 复盘完成 |

### 阶段转换规则

```yaml
transitions:
  spark_to_design:
    condition: 需求文档完成 && 价值评估通过
    gate: 需求完整性检查
  design_to_tasks:
    condition: 设计文档完成 && 三维评审通过
    gate: 设计评审门禁
  tasks_to_build:
    condition: tasks.md 完成 && 任务边界清晰
    gate: 任务合同检查
  build_to_review:
    condition: 代码完成 && 单元测试通过
    gate: 测试覆盖率检查
  review_to_test:
    condition: 审查通过 && 无阻塞性问题
    gate: 审查门禁
  test_to_ship:
    condition: 系统测试通过 && QA 签收
    gate: 测试门禁
  ship_to_reflect:
    condition: 发布成功 && 部署验证
    gate: 发布门禁
  reflect_to_spark:
    condition: 复盘完成 && 经验沉淀
    gate: 复盘门禁
```

### 快速模式

对于小型变更，支持快速模式（跳过非必要阶段）：

```
Spark → Tasks → Build → Ship
```

快速模式条件：
- 变更范围 < 3 个文件
- 不涉及架构变更
- 不涉及外部接口变更
- 用户明确指定快速模式

### 状态持久化

工作流状态持久化到 `.adk/state.json`，支持：
- 中断恢复
- 跨会话交接
- 状态查询

详见 `docs/workflows/lifecycle.md`

## Gate 机制设计原则（VibeFlow 吸收）

> 来源: vibeflow vision.md

### Gate 选择标准

新增 gate 前，必须回答 4 个问题：

1. **这件事是不是 100% 可机械化？** → 脚本化
2. **这件事是不是必须稳定复现？** → 状态机
3. **这件事是不是经常忘，而且忘了会出事？** → Gate
4. **这件事能不能更自然地由 agent runtime、skill 提示词或项目产物来承担？** → 不做 Gate

**前三个问题都答"是"，才做 Gate。**

### 现有 Gate 清单

| Gate | 拦截内容 | 自动化程度 |
|------|----------|-----------|
| 需求完整性检查 | 缺少需求文档 | 半自动 |
| 设计评审门禁 | 设计文档不完整 | 人工 |
| 任务合同检查 | 任务边界模糊 | 半自动 |
| 测试覆盖率检查 | 测试覆盖率不足 | 全自动 |
| 审查门禁 | 阻塞性问题未解决 | 人工 |
| 测试门禁 | 系统测试未通过 | 全自动 |
| 发布门禁 | 发布产物不完整 | 半自动 |
| 复盘门禁 | 复盘未完成 | 人工 |

### Gate 实现原则

1. **Gate 不接管执行** — 只拦截，不自动修复
2. **Gate 有明确的通过标准** — 不依赖主观判断
3. **Gate 支持绕过** — 紧急情况可绕过，但必须记录原因
4. **Gate 有审计日志** — 记录谁在什么时候绕过了哪个 Gate

---

## 仓库深度分析报告 (2026-05-05)

### 功能定位
adk 是面向 ~/.codex 等开发代理运行目录的 Agent/Skill/Profile 生产资产包。核心目标：把参考仓中的优秀方法论压实为可安装、可验证、可回滚、可迭代的工程资产。

### 资产统计
- Agents: 10 个角色（全部 p0 级）
 Core Skills: 33 个（p0:8, p1:14）
 Optional Skills: 9 个（p2 级）
- Profiles: 10 个（core + 7 extends + 2 独立）
- Scripts: 26 个
 Tests: 29 个测试文件，59 个用例
 Docs: 58 个文档 + 26 个 Runbook

### 质量评分: 8.0/10

### 优点
1. 方法论工程化：从"口头约定"压实为可安装、可验证、可回滚的工程资产
2. 嵌入式领域深度：22 个 Core Skill 覆盖嵌入式全栈（寄存器/BSP/RTOS/协议栈/HIL-SIL）
3. Evidence Index 机制：强制"结论必有证据"，解决 AI Agent 输出可信度问题
4. Profile 分层：10 个 Profile 覆盖个人/团队/嵌入式/发布/重构/事故场景
5. 工作流门禁：propose->apply->verify->review->archive 状态机 + 分级评审
6. 多工具支持：codex/claude-code/hermes-agent/opencode 四个工具目标

### 缺点
1. 版本撕裂：manifest(1.0.0) vs README(0.3.0) 不一致
2. 配置冲突：manifest default_mode(symlink) vs README 推荐(copy)
3. 动态路由缺失：runtime routing 是静态文档，缺少运行时路由引擎
4. Evidence Index 纯 Markdown 表格，缺少结构化查询能力
5. 生产运维脚本（monitoring/auto-ops/performance/security）实现深度待验证
6. 42 个文档缺少统一导航索引
7. Profile 冲突检测缺失（两个 optional profile 叠加时的兼容性）
8. 技能间依赖关系未在 manifest 中显式声明

### 可借鉴点（供其他仓库参考）
1. manifest.yaml 单一事实源设计
2. Profile extends 继承机制
3. Evidence Index 命令级证据追加
4. devkit.sh 统一命令入口
5. check_profile_coherence.sh 自动一致性检查

### 资产来源
- 方法论类资产：从外部参考仓吸收并本地化
- 技能格式规范：遵循通用 skill 格式标准
- 门禁协议：基于通用 artifact 门禁机制
- 变更管理：基于通用变更管理流程
