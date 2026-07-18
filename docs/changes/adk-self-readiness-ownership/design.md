# 设计说明：adk-self-readiness-ownership

## 结构

- `AGENTS.md`：保留仓库定位、结构、命令、编码/测试/提交规则、安全硬边界、详细规则索引和当前资产边界摘要。
- `docs/agent-operating-rules.md`：承接 R1-R8、八阶段生命周期和 Gate 机制细节，成为根入口的直接一级链接。
- `OWNERS`：声明 owner、review scope、外部执行边界和复核周期。
- `.adk/harness-readiness.json`：按七维合同记录 owner/date；工具维度保留元数据但在无 MCP 时仍由扫描结果判为 not-applicable。

## 真实性边界

- `last_verified_at` 使用本轮实际验证日期 2026-07-18，并受 90 天 freshness 门禁约束。
- readiness `pass` 只代表 repository evidence projection，不改变 `field_evidence_status=not-verified`。
- OWNERS 不替代 GitHub branch protection、remote review 或第二操作者证据。

## 验证

- `wc -l AGENTS.md` 不超过合同预算。
- 关键规则标题在下沉文档中仍存在，根入口能直接发现链接。
- `harness readiness --root . --as-of 2026-07-18 --gate` 返回 0，六个 pass、一个 not-applicable。
- change governance、format、docs alignment、strict 和 full regression 通过。

## 回滚

恢复原单文件规则与删除 metadata/OWNERS 即可回滚；回滚后 readiness 必须重新显示 oversized/missing ownership blocker，不能保留失真的 pass 报告。
