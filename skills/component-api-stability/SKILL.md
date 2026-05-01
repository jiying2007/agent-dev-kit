---
name: component-api-stability
description: 组件 API 稳定性治理
triggers:
  - 公共组件准备对外复用时
non_triggers:
  - 私有一次性脚本
inputs:
  - 当前 API、调用方清单
outputs:
  - 兼容性评估与演进策略
constraints:
  - 破坏性变更必须附迁移路径
---

# component-api-stability

## Goal
- 建立 API 稳定性基线，控制破坏性变更风险。

## Prerequisites
- 收集 API 使用方清单与版本分布。
- 明确当前语义不稳定点与历史兼容问题。

## Workflow
1. 盘点公开 API：按稳定/试验/废弃分类。
2. 评估兼容影响：识别破坏性变更和行为变更。
3. 制定演进策略：版本号规则、弃用窗口、迁移提示。
4. 设计兼容测试：老版本调用方回归验证。
5. 形成发布建议：可放行条件与阻断项。

## Commands
```bash
rg -n "public|export|deprecated" <component_path>
<project-test-cmd> --filter compatibility
```

## Evidence Template
```md
- API Inventory:
- Breaking Changes:
- Deprecation Window:
- Consumer Impact:
- Compatibility Test Result:
```

## Failure Handling
- 调用方影响无法评估时，强制 `needs-fix`。
- 若发现未声明的 breaking change，阻断发布并补迁移文档。

## Quality Gate
- 必须区分行为变更与签名变更。
- 必须给出调用方影响清单和迁移路径。
- 兼容回归结果必须可追溯到命令或报告。
