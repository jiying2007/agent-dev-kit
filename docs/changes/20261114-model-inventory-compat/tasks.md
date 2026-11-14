# 任务

- [x] M1 记录真实失败、冻结修复范围及不重跑约束；verify：requirements/design绑定准确run/C2/ZIP，区分实际链接路径和未观测目标。
- [x] M2 官方布局核验、最小安全修复和RED/GREEN；verify：官方v0.40.16三份源码身份已绑定；新增模型专用模块，保留通用inventory/发布器/workflow字节。普通与parent-child清单绑定、v2优先、规范raw相对路径、fd-relative/no-follow及严格JSON边界已实现；原通用拒绝RED及草稿3个路径子例RED保留。实际定向36个方法通过，Ruff、格式、mypy的5个文件、module-size/security全部exit0；模型/Docker未重跑。完整回归与最终独立裁决由M3单独判定。
- [x] M3 定向与完整验证、独立Spec/Quality审查；verify：准确源码E86710516、36方法/52子例与102/102完整回归通过，source_drift为空；独立Spec/Quality于2026-11-14T16:45:34Z均PASS、开放发现0，raw链接Major闭合。15项源码和7份回执、27个原始日志成员独立核验；后续root生成的typed记录实际校验PASS，不冒称被预先审过。静态通过不代替原生重测。
- [x] M4 正常提交保存并同步计划；verify：源码E及后续独立审查/验证回执保存于review分支，负结果与局部修复在原计划分别记录；执行分支仍为C2、原run attempt仍1且failure、main仍c57，消费者HEAD仍167b7cb且干净。没有第二次实验、正式发布或消费者锁更新。
