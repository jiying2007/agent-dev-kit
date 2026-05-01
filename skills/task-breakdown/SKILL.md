---
name: task-breakdown
description: 将需求拆解为可并行执行的任务包
triggers:
  - 任务过大或多人协作时
  - 需要评估是否适合并行开发时
non_triggers:
  - 单点微调任务
  - 单文件小修且无共享依赖变更
inputs:
  - 需求范围、里程碑、模块边界与依赖关系
outputs:
  - 任务清单、依赖图、优先级、ownership 与冲突矩阵
constraints:
  - 每个任务必须可独立验证
  - 默认禁止两个任务并行修改同一 shared contract/schema
---

# task-breakdown

## Goal
- 把复杂需求拆成边界清晰、可独立验收的任务包。

## Prerequisites
- 已有需求包和至少一个可执行验收标准。
- 明确共享文件、共享 contract 和根配置触点。

## Workflow
1. 定义拆分边界：明确 scope_write、scope_read、输入输出与完成标准。
2. 并行准入判断：检查是否存在同文件写冲突、共享 contract、根配置冲突。
3. 生成任务包：每个任务给出 owner、依赖、验证命令与阻塞条件。
4. 规划整合顺序：列出 merge order、联调点与最终统一验证步骤。
5. 输出执行建议：适合并行则给 2-4 个任务包，不适合则给单线程方案。

## Commands
```bash
rg -n "contract|schema|shared|entry|router|package.json" <repo_root>
git diff --name-only <base>...HEAD
```

## Evidence Template
```md
- Parallel Suitability: yes/no
- Task Packages (owner/scope/dependency):
- Conflict Matrix:
- Merge Order:
- Final Integration Verification:
```

## Failure Handling
- 若拆分后冲突面扩大，降级为单线程执行方案。
- 若出现未识别共享依赖，暂停并重新划分 scope。

## Quality Gate
- 每个任务必须具备独立验证命令与可交付产物。
- 必须显式标记共享文件/共享 contract 冲突面。
- 必须给出“适合并行/不适合并行”的明确结论与理由。
