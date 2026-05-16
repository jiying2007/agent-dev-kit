---
name: adk-pilot-framework
description: 跨仓库 Pilot 试跑框架——场景定义、证据收集与门禁验收
version: 1.0.0
last_updated: 2026-05-08
triggers:
  - "试跑"
  - "pilot"
  - "真实场景验证"
  - "运行目录验证"
  - "codex 试跑"
non_triggers:
  - 纯本地单元测试（无需运行目录验证）
  - 文档编写或方案讨论
inputs:
  - 待验证能力清单、目标运行目录、场景定义、预期行为
outputs:
  - 试跑报告（场景+证据+结论）
  - 门禁验收结果（pilot-pass / pilot-fail）
  - 回灌建议（采纳/改进/淘汰）
constraints:
  - 无真实运行证据不得声明 pilot 通过
  - 门禁三联证据必须全部 PASS（health-check / global-health / pilot-gate）
  - 失败项必须记录根因并转入调试流程
---

# adk-pilot-framework

## Goal
## Prerequisites

- 理解相关领域的基本概念
- 熟悉项目结构和工作流程
- 具备基本的文档编写能力


在将 adk 资产正式发布前，通过结构化的"场景→试跑→证据→门禁→回灌"闭环，在真实运行目录中验证能力有效性，避免"本地通过但实战失败"。

## 来源说明

- **核心来源**：`llm_agent/AGENTS.md` 中的"D5-D7 codex 实战试跑与回灌"流程
- **Runbook 参考**：`docs/runbooks/codex-runtime-pilot.md`
- **门禁机制**：`scripts/check-adk-harden-readiness.sh --require-pilot`
- **健康检查**：`scripts/health-check.sh` + `scripts/check-global-codex-health.sh`
- **迭代依据**：`AGENTS.md` 第 3 节"先在 agent-dev-kit 完成资产化与验证、再交接到 ~/codex、由 ~/codex apply 到 ~/.codex 试跑、再回灌 adk"双向闭环

## 模式描述

### 1. 试跑场景分类

| 场景类型 | 说明 | 验证重点 | 典型目录 |
|----------|------|----------|----------|
| 功能开发 | 新功能从零实现 | Skill 触发准确率、输出质量 | `~/codex -> ~/.codex` |
| 缺陷修复 | 已知 bug 修复 | 调试流程完整性、修复验证 | `~/codex -> ~/.codex` |
| 重构 | 大规模代码重构 | 回归测试覆盖、破坏性变更检测 | `~/codex -> ~/.codex` |
| 发布 | 版本发布流程 | 版本号、changelog、门禁全通过 | `agent-dev-kit` |
| 跨仓协作 | 多仓联动变更 | 交接协议、artifact 完整性 | 多仓 |

### 2. 试跑执行流程

```
场景定义 → 能力安装 → 真实执行 → 证据收集 → 门禁验收 → 回灌决策
```

**Step 1: 场景定义**
```md
[pilot-scenario]
id: pilot-<date>-<seq>
type: feature | bugfix | refactor | release | cross-repo
target_dir: ~/codex | ~/.codex | <project-dir>
skills_under_test:
  - <skill-1>
  - <skill-2>
expected_behavior: <预期行为描述>
success_criteria: <可量化验收标准>
```

**Step 2: 能力安装**
```bash
bash scripts/devkit.sh install --tool codex --profile core
# 如需额外能力
bash scripts/devkit.sh install --tool codex --profile core --extra-profile <profile>
```

**Step 3: 真实执行**
- 在目标目录执行真实任务
- 记录所有命令、输出、异常
- 禁止事后补写或美化日志

**Step 4: 证据收集**
```bash
# 三联门禁证据
bash scripts/health-check.sh ~/.codex minimal
bash scripts/check-global-codex-health.sh ~/.codex minimal
bash scripts/check-adk-harden-readiness.sh . --require-pilot --skip-full-suite
```

**Step 5: 门禁验收**
- 三联证据必须全部 PASS
- 任一失败 → pilot-fail，转入调试

**Step 6: 回灌决策**

| 结果 | 决策 | 动作 |
|------|------|------|
| 全部 PASS 且行为符合预期 | 采纳 | 升级为 adk 默认推荐 |
| PASS 但行为有偏差 | 改进 | 记录偏差，优化后重跑 |
| FAIL 且根因明确 | 修复 | 修复后重跑 |
| FAIL 且根因不明 | 淘汰 | 记录负结果，降级或移除 |

### 3. 试跑报告模板

```md
# Pilot Report: pilot-<date>-<seq>

## 场景
- 类型: <type>
- 目标目录: <target_dir>
- 测试能力: <skills_under_test>

## 执行记录
| 步骤 | 命令 | 结果 | 证据路径 |
|------|------|------|----------|
| ... | ... | ... | ... |

## 门禁结果
- health-check: PASS / FAIL
- global-health: PASS / FAIL
- pilot-gate: PASS / FAIL
- 最终结论: pilot-pass / pilot-fail

## 回灌建议
- 采纳: <list>
- 改进: <list>
- 淘汰: <list>

## 负结果记录
- <失败项 + 根因 + 影响>
```

### 4. 门禁硬约束

1. **三联证据**：health-check / global-health / pilot-gate 必须全部 PASS
2. **禁止事后补证据**：所有证据必须在试跑时实时记录
3. **失败即停止**：任一门禁失败，不得继续后续步骤
4. **回灌闭环**：试跑结果必须回写 `subrepos/adoption-matrix.md`

## Commands

```bash
# 安装试跑能力
bash scripts/devkit.sh install --tool codex --profile core

# 健康检查三联
bash scripts/health-check.sh ~/.codex minimal
bash scripts/check-global-codex-health.sh ~/.codex minimal
bash scripts/check-adk-harden-readiness.sh . --require-pilot --skip-full-suite

# 生成试跑报告
bash scripts/generate-weekly-report.sh --pilot
```

## Workflow

1. 定义试跑场景（目标运行目录、预期行为、验收标准）
2. 准备试跑环境（隔离配置、基线快照）
3. 执行试跑（运行能力、收集证据）
4. 门禁验收（health-check / global-health / pilot-gate 三联）
5. 记录结果（pass/fail + 根因 + 负结果留痕）
6. 回灌建议（采纳/改进/淘汰 → 更新 adoption-matrix.md）

## Quality Gate

1. 无真实运行证据不得声明 pilot 通过
2. 门禁三联证据必须全部 PASS（health-check / global-health / pilot-gate）
3. 失败项必须记录根因并转入调试流程
4. 负结果必须留痕（negative-results.md）
5. 回灌建议必须有具体证据支撑

## 待完善事项

- [ ] 试跑场景自动发现（从 AGENTS.md 意图路由表自动生成场景）
- [ ] 试跑报告结构化存储（当前为 Markdown，缺少查询能力）
- [ ] 多轮试跑对比分析（同一能力在不同版本的行为差异）
- [ ] 试跑环境自动隔离（避免试跑污染正式配置）
- [ ] 试跑结果自动回灌到 adoption-matrix.md
