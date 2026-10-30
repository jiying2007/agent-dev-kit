# 取消期间保留事务恢复材料：设计

## 决策

1. 发布开始前进入保留恢复材料状态，完整成功或完整补偿后才允许清理。
2. install apply 默认保留 staging；收据已提交或补偿完整完成后才解除保留。
3. 取消不被伪装为成功；未完成安装继续被既有 staging guard 拒绝。

## 影响入口

- `src/agent_dev_kit/atomic_io.py`
- `src/agent_dev_kit/installation_transaction.py`
- `tests/test_cancellation_recovery.py`
- `tests/test_install.sh`

## 迁移与回滚

保持现有公共入口和权限边界；实现与回归一起审查、一起回退。已有历史证据不重写。源码与普通本地/公开 CI 验证不生成 native、field、effect 或产品资格。

## 验证与审核边界

复用现有定向测试与受保护 CI；独立 Spec/Quality 审核仍需真实独立执行。本轮不新增 Codex/Work 或代理委派，不把实现者自检登记为独立审核。
