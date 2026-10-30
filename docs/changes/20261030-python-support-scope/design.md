# 区分 Python 兼容与验证范围：设计

## 决策

1. 复用 doctor 的环境报告，保留兼容字段并附加明确兼容含义、CI 验证范围与生命周期信息。
2. 以固定版本生命周期数据表达已知 EOL；未知或未验证版本不可自动宣称已通过项目 CI。
3. launcher 对旧兼容版本给出可操作提示；既有最低版本 strict 语义保持，文档说明其非安全维护承诺。

## 影响入口

- `src/agent_dev_kit/doctor.py`
- `scripts/devkit.sh`
- `tests/test_python_launcher.sh`
- `README.md`

## 迁移与回滚

保持现有公共入口和权限边界；实现与回归一起审查、一起回退。已有历史证据不重写。源码与普通本地/公开 CI 验证不生成 native、field、effect 或产品资格。

## 验证与审核边界

复用现有定向测试与受保护 CI；独立 Spec/Quality 审核仍需真实独立执行。本轮不新增 Codex/Work 或代理委派，不把实现者自检登记为独立审核。

