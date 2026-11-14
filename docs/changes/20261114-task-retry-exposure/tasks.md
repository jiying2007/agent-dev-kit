# 任务

- [x] T1 保存原缺陷的确定性 RED 与有效控制；verify：`evidence/red.json` 保留7项新增回归和2项控制的原始执行；旧实现出现13个子案例error和1个failure，均为重复名称拒收。
- [x] T2 修复重复过程观测的运行级投影，并补导入与配对回归；verify：相同命令GREEN 9/9，run-evidence 49项、effect-trials 35项通过；完整原始日志及四文件摘要见 `evidence/frozen.json`。一致重复加载可接受，身份/摘要/primary/对照冲突仍拒绝，同名过程失败不被覆盖，全部证据逐条验证，重试成本完整、first-pass=false。
- [x] T3 更新操作说明和补丁版本投影，执行适用静态与完整回归；verify：源码 `948f49b2ca3ecc56c9632946b67736b0c0047a14` 的27份变更逐字节核对；本地完整回归102/102，strict validate、完整Ruff与module-size通过；promotion入口的本地导入环境修正后通过。日志见 `evidence/`；受保护HEAD CI仍单独验收。
- [x] T4 独立只读 Spec/Quality 审查并绑定精确源码；verify：独立审查pass，open blocker/major/minor均0；现有typed校验器通过。首次回执因UTC后缀不是canonical Z被拒绝，仅将+00:00改为等价Z后通过，原始时刻和校验器未变。完整差异及原始验证日志分别绑定，不授予模型效果或发布资格。
- [ ] T5 受保护合并、主线 CI、不可变 Release 和消费者 source-only 晋级；verify：每个仓库的最终 SHA 与新鲜检查分别核对。

T6 真实宿主任务试验沿用原方案，单独判断可执行性；本修复不构成其已完成证据。
