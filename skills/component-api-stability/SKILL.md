---
name: component-api-stability
description: 组件 API 稳定性治理
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "API稳定性"
  - "组件API"
  - "接口兼容"
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

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
