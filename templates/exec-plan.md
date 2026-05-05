# 执行计划: {{title}}

> 执行计划模板 — 六要素结构

- **owner**: {{agent_name}}
- **date**: {{YYYY-MM-DD}}
- **status**: draft | in-progress | completed

## 1. 目标

{{描述本次变更的目标，要解决什么问题}}

## 2. 范围

### 包含
- {{scope_included_1}}

### 不包含
- {{scope_excluded_1}}

## 3. 风险评估

| # | 风险 | 概率 | 影响 | 缓解措施 |
|---|------|------|------|---------|
| 1 | {{risk}} | 高/中/低 | 高/中/低 | {{mitigation}} |

## 4. 决策记录

| # | 决策 | 原因 | 备选方案 | 放弃原因 |
|---|------|------|---------|---------|
| 1 | {{decision}} | {{reason}} | {{alternative}} | {{why_not}} |

## 5. 验证路径

### Evidence Index

| 命令 | 退出码 | 结果摘要 | 证据路径 | 层级 |
|------|--------|---------|---------|------|
| {{command}} | {{exit_code}} | {{summary}} | {{evidence_path}} | Agent/Skill/Workflow |

### 验证步骤
1. {{step_1}}
2. {{step_2}}

## 6. 完成结果

### 结果摘要
{{总结完成情况}}

### 经验教训
- {{lesson_1}}

### 后续事项
- [ ] {{follow_up_1}}
