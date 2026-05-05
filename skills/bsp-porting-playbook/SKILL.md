---
name: bsp-porting-playbook
description: BSP 移植流程与风险控制
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - SoC/板卡迁移或内核升级时
non_triggers:
  - 仅业务代码改动
inputs:
  - 旧平台信息、新平台约束
outputs:
  - 移植步骤与验证矩阵
constraints:
  - 先最小可启动，再扩展外设
---

# bsp-porting-playbook

## Goal
- 在可控风险下完成 BSP 迁移，并保留回退路径。

## Prerequisites
- 明确旧/新平台差异（CPU、时钟树、内存映射、驱动依赖）。
- 约定迁移范围与阶段里程碑。

## Workflow
1. 平台差异矩阵：内核配置、设备树、驱动依赖逐项比对。
2. 最小可启动路径：启动链路、控制台、存储、网络基础能力。
3. 外设分阶段接入：按关键业务优先级逐步上线。
4. 回归验证：启动时间、稳定性、关键功能与功耗指标。
5. 发布前收口：输出遗留风险与后续补齐计划。

## Commands
```bash
<kernel-build-cmd>
<boot-log-cmd> | tail -n 200
<smoke-test-cmd> --platform <new_board>
```

## Evidence Template
```md
- Diff Matrix (old vs new):
- Bring-up Milestones:
- Device Enablement Status:
- Regression Result:
- Rollback Plan:
```

## Failure Handling
- 内核无法启动时，回退到上一个可启动配置并做二分定位。
- 外设接入引入系统不稳定时，按模块回滚并隔离问题。

## Quality Gate
- 必须先达到“最小可启动”再进入功能扩展阶段。
- 每个里程碑必须包含验证结果与阻塞项。
- 必须提供已验证回退路径。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
