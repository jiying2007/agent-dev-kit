# 任务与检查点

- [x] 核实main基线、局部规则、clean状态及原官方失败证据。
- [x] 原定向基线4/4通过。
- [x] 新敌意环境回归在原创建流程commit阶段失败：invalid date format，exit128；不是cleanup根因复现。
- [x] 最小helper隔离，保留生产和原身份断言；定向5/5通过。
- [ ] 冻结差异后完整回归及源外证据记录。
- [ ] 差异审查、提交和托管矩阵门禁。

owner为当前执行线程；单仓串行，无并行代理。完整结果记录于source外的检查点，避免验证后修改source快照。每阶段失败先定位，不盲目重跑；最多一次有依据的环境重试，根因不明则保留needs-review。许可证恢复在独立Codex阶段，不在本change编造归属或授权。

## 版本门禁修正

旧7.14.1测试候选本地full97/97通过，但PR175 run37394472190的contract-py3.11明确拒绝source version7.14.1到7.14.1。初始范围遗漏README和CI的每次合并require-advance；修正为7.14.2所有既有版本投影及campaign ID同步，不放宽门禁。旧full不重标为新source的验证。
