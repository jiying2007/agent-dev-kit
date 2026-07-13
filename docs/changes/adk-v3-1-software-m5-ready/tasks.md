# 执行任务：adk-v3-1-software-m5-ready

- [x] 需求确认与边界冻结
- [x] 升级 3.1 版本源并实现 doctor/campaign/certifier
- [x] 实现 export/install/rollback writer lock 与并发恢复
- [x] 实现 local release rehearsal 与兼容债务门禁
- [x] 扩展 60 条评测集并补充 fake-runtime/负向测试
- [ ] 在 `$150` 上限内执行 Codex/Claude campaign（Claude 未认证，按合同阻断）
- [x] 完成本地验证（lint/test/smoke/full regression/source build/wheel/rehearsal）
- [x] 代码评审与分级闭环（blocker/major/minor）
- [x] 文档同步与根仓 M5 certifier 集成
- [ ] 提交与远端核验

## Ownership 与并行冲突检查
- 写入范围：ADK 3.1 control plane、tests、change docs；随后根仓 M5 contract/pilot/scorecard。
- 读取范围：两个仓全部 source/test/docs 与只读 runtime 状态。
- 是否与其他任务冲突：单代理串行；三个 dirty reference 仓禁止写入。

## 轻量工件与收敛结论
- 需求梳理工件：`proposal.md`、`design.md`。
- task checklist 工件：本文件。
- 执行反馈/验收记录工件：`negative-results.md`、后续 `verify-report.md`、runtime campaign evidence。
- 收敛结论或阻塞说明：即时最多 M4/M5-ready；30 天独立 pilot 未完成前 M5 固定阻断。
