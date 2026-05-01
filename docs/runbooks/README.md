# Runbooks

按场景提供可直接执行的 Agent/Skill 组合与命令序列，默认遵循 `propose -> apply -> verify -> archive`。

## 场景列表

- `feature-delivery.md`：需求到交付
- `driver-bringup.md`：新外设驱动上板联调
- `release-hardening.md`：发布前收口与风险压实

## 使用方式

1. 先执行 `bash scripts/devkit.sh catalog build`，确认当前可用能力。
2. 按场景文档选择 Agent 流程与 Skill 组合。
3. 执行对应命令模板，并在 `docs/changes/<change-id>/` 留存工件。
