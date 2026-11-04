# adk-pilot-framework — 补充参考资料

此参考文件只提供可选背景、示例和检查提示；当前能力流程、权限、回退与放行结论以 `../SKILL.md`、Manifest 及运行时门禁为准。示例命令不得被解释为写权限授权。

## 来源说明

- **核心来源**：`llm_agent/AGENTS.md` 中的"D5-D7 实战试跑与回灌"流程
- **Runbook 参考**：`docs/runbooks/production-deployment.md`
- **门禁机制**：`scripts/check-adk-harden-readiness.sh --require-pilot`
- **健康检查**：`scripts/health-check.sh` + target-specific smoke checks
- **迭代依据**：`AGENTS.md` 第 3 节"先在 agent-dev-kit 完成资产化与验证、再交接到显式 tool target 试跑、再回灌 adk"双向闭环

## 模式描述

### 1. 试跑场景分类

| 场景类型 | 说明 | 验证重点 | 典型目录 |
|----------|------|----------|----------|
| 功能开发 | 新功能从零实现 | Skill 触发准确率、输出质量 | 显式 tool target |
| 缺陷修复 | 已知 bug 修复 | 调试流程完整性、修复验证 | 显式 tool target |
| 重构 | 大规模代码重构 | 回归测试覆盖、破坏性变更检测 | 显式 tool target |
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
target_dir: <tool-target-dir> | <project-dir>
skills_under_test:
  - <skill-1>
  - <skill-2>
expected_behavior: <预期行为描述>
success_criteria: <可量化验收标准>
```

**Step 2: 能力交接**
```bash
bash scripts/devkit.sh convert --target claude-code --out /tmp/adk-handoff --profile personal-core
bash scripts/devkit.sh runtime-boundary
```

**Step 3: 真实执行**
- 在目标目录执行真实任务
- 记录所有命令、输出、异常
- 禁止事后补写或美化日志

**Step 4: 证据收集**
```bash
# 三联门禁证据
bash scripts/health-check.sh <tool-target-dir> minimal
bash scripts/devkit.sh runtime-boundary
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
