# 第三阶段独立复验（94d68e7 冻结已因回归失效）

审查者继续只读产品源码。观察的第一次 source commit 为 `94d68e7501427fc518a0804b6b8f258e4b12f134`，不对其签发 canonical pass。

## 已独立确认

- 原 30 项独立路由探针 fresh 复跑为 30/30：IR-2 的四项禁止创建表达与 IR-3 的原六项被解释/审查对象均已修复。
- trigger matrix 31 tests、runtime comparison 15 tests、materializer 10 tests 通过。
- provider missing-safety/missing-cost 回归移入已有 runtime comparison 测试模块，使用真实既有记录语义，不执行 provider，没有增加不受 campaign 支持的 runtime，也没有更改 scanner。
- 移除的私有 `_phrase_matches` / `_phrase_match` / `_contains_phrase` 与原内核 formatter 经调用点检索不存在遗留依赖；formatter 的行为迁移已在前阶段独立 AST 核对。

## IR-3 残留回归：顺序动作被解释作用域吞掉（major / open）

新的 `_is_mentioned_action` 可以在“然后”“接着”“并”等边界后恢复肯定动作，但漏掉自然的“先……再……”顺序表达。

| 输入 | 基线实际 | 94d68e7 实际 |
| --- | --- | --- |
| 先说明方案再实现驱动 | driver implementation / workspace-write | abstain / deny |
| 先解释隔离价值再创建 worktree | worktree governance / deny | abstain / deny |
| 请先解释取舍再更新 ADR | ADR writer / deny | abstain / deny |

另外 `先说明方案再实现 RTOS SPI DMA 驱动` 也被错误 abstain，而同义的 `请先解释取舍然后更新 ADR` 正确选择 ADR。

这不是新增任意领域要求，而是新解释过滤器对明确顺序请求的相邻回归，违背保持同句肯定动作与已有正确行为的要求。
建议按有界顺序语法处理，并保留 `解释为什么再实现……` 等仍属于解释对象的反向控制；不能全局遇到“再”就结束解释作用域。

独立原始证据：

- `routing-boundary-probes-reverified-30.json`
- `trigger-matrix-tests-reverified.txt`
- `runtime-comparison-tests.txt`
- `campaign-materializer-tests-reverified.txt`
- `routing-sequential-controls.json`
- `routing-sequential-controls-baseline.json`

协调者已确认此第一次源码冻结失效，将保留旧 patch、停止该次本地完整回归并在原实施者修复后重新生成精确源码身份及完整验证证据。
