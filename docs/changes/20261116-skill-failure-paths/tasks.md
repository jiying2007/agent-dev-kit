# 任务与状态

当前阶段：五项实现及定向验证完成，完整基线/来源对账完成；新 CMake 消费者已实际交付 B 产物并保留旧构建。正在冻结集成源码，随后执行完整回归和最终独立审查。此处记录源码冻结前状态，后续准确结果在 `verification.md` 及对应原始回执追加。

- [x] 三组逐文件审查现有 65 个 Skills；verify：合并清单与 Git population/字节摘要相等，逐项决定完整。
- [x] 核验外部候选并筛选实际缺口；verify：固定来源、许可、具体反例及采用/拒绝依据可复核。
- [x] 冻结选定问题的需求/设计/验收后分派实现；verify：每项修改对应明确失败路径和最小写集。
- [x] F1/F2：修扫描输出与中断采样；verify：发布命令的 sentinel/候选/exit 1/2 和单轮终止/正常多轮矩阵。
- [x] F3：修 CMake 身份复用指导；verify：真实旧目录错误身份、新目录正确身份、强制重编译与消费者任务。
- [x] F4/F5：修 schema 方言/组合边界及空审核模板；verify：真实 validator 输入矩阵和导出表格。
- [x] 运行针对性方法验证与必要的新消费者任务；verify：原失败、正常控制、真实输出和环境边界全部保留。
- [ ] 冻结源码并执行必要完整回归和预算检查；verify：准确 commit/tree、真实命令/退出码/时间及 unchanged thresholds。
- [ ] 独立 Spec/Quality 审查与证据包装核验；verify：不同实施/审查身份、原材料摘要和准确目标源码绑定。
- [ ] 完成 ADK 受保护合并、fresh main CI 和正式资产核验；verify：不可变 release、tag/commit、实际三资产及契约相符。
- [ ] 完成 Root source-only 接入及合并后验证；verify：准确两文件变更、完整回归、PR/main 跨仓 attestation CI 成功。

下一动作：冻结源码并执行完整回归/8 profile 检查；取得独立 Spec/Quality 与证据包装裁决；按原保护完成发布和 Root source-only 接入。
