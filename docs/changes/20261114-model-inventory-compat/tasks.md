# 任务

- [x] M1 记录真实失败、冻结修复范围及不重跑约束；verify：requirements/design绑定准确run/C2/ZIP，区分实际链接路径和未观测目标。
- [x] M2 官方布局核验、最小安全修复和RED/GREEN；verify：官方v0.40.16三份源码身份已绑定；新增模型专用模块，保留通用inventory/发布器/workflow字节。普通与parent-child清单绑定、v2优先、规范raw相对路径、fd-relative/no-follow及严格JSON边界已实现；原通用拒绝RED及草稿3个路径子例RED保留。实际定向36个方法通过，Ruff、格式、mypy的5个文件、module-size/security全部exit0；模型/Docker未重跑。完整回归与最终独立裁决由M3单独判定。
- [ ] M3 定向与完整验证、独立Spec/Quality审查；verify：精确源码/原件、真实命令结果、开放重大问题为0；静态通过不代替原生重测。
- [ ] M4 正常提交保存并同步计划；verify：执行分支仍为C2、run attempt仍1、正式发布和消费者锁未变，负结果与局部修复均可追溯。
