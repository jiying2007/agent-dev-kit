---
name: integration-hil-sil
description: HIL/SIL 集成验证编排
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - "集成测试"
  - "HIL测试"
  - "SIL测试"
non_triggers:
  - 只改注释文档
inputs:
  - 系统拓扑、测试资源
outputs:
  - HIL/SIL 用例矩阵
constraints:
  - 必须标注硬件依赖与替代方案
---

# integration-hil-sil

## Goal
- 通过 HIL/SIL 组合验证系统级行为和回归稳定性。

## Prerequisites
- 明确系统拓扑、接口依赖和硬件资源占用计划。
- 定义 HIL 与 SIL 的覆盖边界和切换条件。

## Workflow
1. 分层建模：模块级（SIL）与系统级（HIL）用例划分。
2. 编排用例矩阵：功能、性能、异常恢复三类场景。
3. 环境校准：时钟同步、数据回放、设备映射一致性。
4. 执行验证：先 SIL 快速回归，再 HIL 关键链路验收。
5. 结果汇总：输出失败模式、复现路径与修复优先级。

## Commands
```bash
<sil-runner-cmd> --suite core
<hil-runner-cmd> --suite critical --hardware <rig_id>
```

## Evidence Template
```md
- Coverage Split (HIL/SIL):
- Environment Baseline:
- Case Result Summary:
- Failure Repro Steps:
- Release Readiness:
```

## Failure Handling
- HIL 资源不可用时，先以 SIL 保持回归连续性并标注风险。
- HIL/SIL 结果冲突时，优先核对环境差异与 mock 假设。

## Quality Gate
- 必须说明 HIL 与 SIL 的覆盖分工。
- 必须至少包含 1 条系统级异常恢复验证。
- 发布前必须给出“可发布/不可发布”明确结论。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
