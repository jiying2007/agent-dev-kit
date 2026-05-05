---
name: requirements-triage
description: 将需求转为可实现、可验证的工程条目
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "需求不清楚"
  - "需求模糊"
  - "需求不明确"
  - "跨团队需求"
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

## 与 grill-with-docs 的区别
- requirements-triage: 需求结构化拆解与验收标准固化
- grill-with-docs: 烤问式需求对齐，通过提问消除模糊

## Quality Gate
- 输出必须包含目标、非目标、影响面、验收标准四项。
- 至少给出一个关键风险及对应验证方式。
- 若充分性检查未通过，结论必须为 `needs-fix`，并列出缺失信息。

---

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "需求已经很清楚了" | 模糊需求是 bug 的温床，口头"清楚"不等于书面可验证 | 按 SKILL.md 流程结构化拆解为目标/非目标/验收标准 |
| "这个需求太简单不需要拆" | 简单需求同样可能隐含边界条件和影响面 | 至少完成充分性检查与影响面分析 |
| "用户说了就这样做" | 用户描述的是期望，不是规格 | 转化为可测试的工程条目并获得确认 |
