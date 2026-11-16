# 任务与当前状态

状态：独立设计核验、Build 与共同定向验证已完成，准备冻结精确源码。此文件保留冻结时状态；后续完整回归、独立审查与交付结果追加到 verification.md 和真实 PR/Release 回执。

- [x] T0：核验远端/工作树基线、规则、近轮变更；完成分组只读审计和受控探针。
- [x] T1 diagnostic_methods：故障入口3558 bytes；6项新host/合同测试覆盖正常、未命中、不可观测、命中恢复、错误清理与原授权要求。
- [x] T2 task_data_methods：IMAP条件分支与7项新本地协议测试完成；真实执行日级/跨时区/字段/边界/缺失/非法/未知时区/预算partial，原只读合同保留。
- [x] T3 diagnostic_methods：原聚合各注册一次；现有版本机制前移11.3.12及必要身份投影；14项共同定向（13项新增+1项原合同）、strict、8个原Profile预算与99文件Claude Code导出通过，未改阈值或预注册判据。
- [ ] T4 parent + independent consumer：冻结源身份、一次最小上下文方法消费观察、完整回归及独立 Spec/Quality 审查；失败保留并按具体发现修复。
- [ ] T5 parent：无损归档原始证据；受保护 PR、精确 main CI、实际 Release 及 Root source-only 接入；按观察到的结果更新本状态。

下一动作：冻结正式源提交并执行T4；保留独立审查及消费观察；推进T5受保护交付。

前置原始审计在 /workspace/scratch/2d4d08f07657/other-skills-{embedded,diagnostic,task-data}-audit。最终随本 change 保存可独立解码的原始证据与来源清单。
