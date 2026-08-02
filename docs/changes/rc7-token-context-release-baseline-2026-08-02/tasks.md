# 任务：RC7 Token 与上下文治理 release baseline

- [x] T1 冻结 RC7 版本决策、范围、提交边界、阶段门禁与回退锚点。
- [x] T2 同步 RC7 版本、migration、campaign contract、测试与 changelog。
- [x] T3 提交并推送 Hub/Codex 任务范围变更。
- [x] T4 提交 ADK release source，并运行 Python 3.11/3.12 full parity。
- [x] T5 从 exact source commit 双构建 artifact，验证字节与 checksum 一致。
- [x] T6 执行 RC6→RC7→rollback rehearsal，验证 RC6 managed hashes 恢复。
- [x] T7 固化 ADK evidence，并验证 source→evidence mapped path diff 为空。
- [ ] T8 同步根仓 release evidence，运行 release-clean full，提交并推送。
- [ ] T9 复核四仓 upstream、残留 dirty、无 tag/Release/active promotion。

## 收敛控制

- retry budget：每个根因最多 2 次。
- staleness threshold：相关 HEAD、artifact checksum 或 staged scope 改变即停止。
- stop condition：`pass | replan | blocked | abort`。

## Ownership 与并行冲突检查

- owner：leiwenjun；implementer：Codex 当前会话。
- scope_write：ADK Token/context 与 RC7 release 工件；Codex/Hub 对应实现；根仓 release policy/evidence/gitlink。
- scope_read：RC6 artifact、历史 release evidence、四仓 upstream 与当前验证产物。
- must_not_touch：个人笔记、三个 reference dirty、Hermes、cache、tag、远端 Release、active promotion。
- shared contract：版本、artifact、rehearsal、root policy 串行执行，不并行写入。
- blocking condition：远端 ahead、RC6 checksum 失败、artifact 不可复现、rehearsal 或 full gate 连续两次失败。
- output contract：commit SHA、artifact SHA256、rehearsal JSON、release evidence、full gate 与 upstream 对齐结果。

## 轻量工件与收敛结论

- planning：proposal、design、tasks、state、migration。
- evidence：negative-results、release-rehearsal、verify/review report、root release evidence 与 cross-repo bundle。
- completion claim：只声明 RC7 source/local release baseline 与已授权 source push；不声明 tag、artifact 发布、runtime/M5/field certification。
