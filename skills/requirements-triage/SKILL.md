---
name: requirements-triage
description: 将需求转为可实现、可验证的工程条目
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 收到模糊需求或跨团队需求时
  - 需求存在多解且边界不清时
non_triggers:
  - 纯代码风格调整
  - 已有完整计划且只需按计划执行
inputs:
  - 需求描述、上下文约束、现有代码入口
outputs:
  - 结构化需求清单、验收标准、非目标与风险清单
  - skill 路由建议（core/optional）与触发优先级
constraints:
  - 不得跳过边界与非目标声明
  - 信息不足时不得直接进入实现
---

# requirements-triage

## Goal
- 将模糊需求收敛为可实现、可验证、可拆分的执行包。

## Prerequisites
- 确认需求来源、owner、时间窗口和关键依赖方。
- 获取最小上下文：入口代码、现有行为、已知限制。

## Workflow
1. 结构化快速扫描：定位模块入口、现有实现、相关测试与依赖约束。
2. 识别关键疑问：列出阻塞规划的问题，并按高/中/低优先级排序。
3. 上下文充分性检查：确认接口契约、风险点、验证方式均可陈述。
4. 触发路由判断：输出 core/optional 技能建议、触发理由与排除理由。
5. 迁移/配置判定：若涉及阶段迁移或配置变更，补里程碑与配置范围判定。
6. Spec 链路判定：补齐 requirements/design/tasks 的最小链路与追溯关系。
7. 产出需求包：目标、非目标、影响面、验收标准、回退条件。
8. 明确下一步：给出可执行任务切分与责任边界（owner/scope）。

## Commands
```bash
rg -n "TODO|FIXME|HACK|deprecated" <target_path>
rg -n "test|spec|contract|schema" <target_path>
bash scripts/devkit.sh match --skill <skill-name> --text "<需求片段>"
```

## Evidence Template
```md
- Goal / Non-goal:
- Impact Scope:
- Acceptance Criteria:
- Migration/Config Decision:
- Spec Chain Decision:
- Install Scope Decision:
- Skill Routing (core/optional + reason):
- Key Risks:
- Missing Context:
- Suggested Task Breakdown:
```

## Failure Handling
- 上下文不足时输出 `needs-fix` 并列出待补信息，不进入实现。
- 若需求混入多个无关问题，先拆分再继续。

## Quality Gate
- 输出必须包含目标、非目标、影响面、验收标准四项。
- 至少给出一个关键风险及对应验证方式。
- 若充分性检查未通过，结论必须为 `needs-fix`，并列出缺失信息。
