# 任务

- [x] T1 保存原缺陷的确定性 RED 与有效控制；verify：`evidence/red.json` 保留7项新增回归和2项控制的原始执行；旧实现出现13个子案例error和1个failure，均为重复名称拒收。
- [x] T2 修复重复过程观测的运行级投影，并补导入与配对回归；verify：相同命令GREEN 9/9，run-evidence 49项、effect-trials 35项通过；完整原始日志及四文件摘要见 `evidence/frozen.json`。一致重复加载可接受，身份/摘要/primary/对照冲突仍拒绝，同名过程失败不被覆盖，全部证据逐条验证，重试成本完整、first-pass=false。
- [ ] T3 更新操作说明和补丁版本投影，执行适用静态与完整回归；verify：当前源码 fresh 结果，不放宽门禁。
- [ ] T4 独立只读 Spec/Quality 审查并绑定精确源码；verify：所有 blocker/major 解除，证据记录保留真实时间与原始来源。
- [ ] T5 受保护合并、主线 CI、不可变 Release 和消费者 source-only 晋级；verify：每个仓库的最终 SHA 与新鲜检查分别核对。

T6 真实宿主任务试验沿用原方案，单独判断可执行性；本修复不构成其已完成证据。
