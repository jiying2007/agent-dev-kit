---
name: <skill-name>
description: <skill 描述>
triggers:
  - <触发条件1>
non_triggers:
  - <不触发条件1>
inputs:
  - <输入项1>
outputs:
  - <输出项1>
constraints:
  - <约束项1>
---

# <skill-name>

## 使用说明
- 用途: 创建新 Skill 时使用此模板作为骨架
- 填写: 替换 frontmatter 字段和 body 中的 [bracket] 占位符
- 触发词: triggers 必须使用可匹配关键词，不要写描述性句子
- 工具: 由 devkit.sh install 安装到目标工具目录

## Goal
- <目标>

## Workflow
1. <步骤1>
2. <步骤2>
3. <步骤3>
4. <输出验证证据与未闭环项>

## Quality Gate
- <验证标准>
- 必须可追溯到输入、实验/验证动作与最终结论
- 未提供验证证据时，结论必须为 `needs-fix`

## Anti-Patterns
- 跳过边界定义直接实现
- 无证据宣称“已完成/已通过”
- 把多个无关问题打包为同一改动
