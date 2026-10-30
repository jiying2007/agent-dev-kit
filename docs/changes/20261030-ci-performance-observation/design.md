# 对照本次 CI 全量耗时：设计

## 决策

1. 复用 check-performance-budgets.sh 和 regression timing 文件。
2. 报告 pass/warn、elapsed_ms、budget_ms 与执行环境，加入 job summary 并与 timing 一并上传。
3. 测试失败或 timing 缺失仍保留显式诊断，不能生成虚假的 observed=0 成功。

## 影响入口

- `.github/workflows/ci.yml`
- `tests/test_performance_budgets.sh`
- `docs/commands.md`

## 迁移与回滚

保持现有公共入口和权限边界；实现与回归一起审查、一起回退。已有历史证据不重写。源码与普通本地/公开 CI 验证不生成 native、field、effect 或产品资格。

## 验证与审核边界

复用现有定向测试与受保护 CI；独立 Spec/Quality 审核仍需真实独立执行。本轮不新增 Codex/Work 或代理委派，不把实现者自检登记为独立审核。

