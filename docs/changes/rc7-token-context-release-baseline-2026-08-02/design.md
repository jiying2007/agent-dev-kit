# 设计：RC7 release baseline

## 版本与提交模型

1. Hub 与 Codex 先提交各自任务范围变更，保留个人与无关 dirty。
2. ADK release source commit 包含实现、测试、版本、migration、campaign contract 和本计划工件。
3. 从 release source commit 的隔离 checkout 两次构建 artifact，要求 tarball 字节一致。
4. 使用 RC6 artifact 作为 previous，执行 `rc.6 -> rc.7 -> rollback`。
5. ADK evidence commit 只增加 rehearsal、verify/review/checklist，不修改 `agents/skills/optional-skills/workflows/templates`。
6. 根仓 gitlink 指向 ADK evidence commit，release evidence 指向 ADK source commit。

## 阶段门禁

| 阶段 | 退出条件 | 回退锚点 |
|---|---|---|
| baseline-aligned | RC7 identity、scope 与 RC6 artifact checksum 有效 | `agent-dev-kit@cf082b6` 与 RC6 artifact |
| migrate-ready | source commit full parity、双构建、rehearsal 全通过 | checksum-bound RC6 artifact |
| cutover-ready | ADK evidence/root release-clean 全通过并推送 | 正常 `git revert` + RC6 artifact |

## 提交边界

- Hub：工具、测试、两条 ADK reviewing candidate 及其索引；排除个人 TXT 阅读器条目。
- Codex：token-lean catalog、workflow activation、plan v3、usage projection、测试与同步规则。
- ADK source：当前 Token/context 实现和 RC7 source identity。
- ADK evidence：只写 release/review 证据。
- Root：双模式门禁、跨仓 bundle、RC7 policy/status/rehearsal/gitlink；排除 reference dirty、cache 与独立仓。

## 失败边界

- 版本身份漂移、artifact 不一致、回滚 hash 漂移、full gate 失败或远端 ahead 时立即停止。
- push 使用当前 upstream；任何 non-fast-forward 不 rebase、不 force push。
- source commit 后若 mapped asset 再变化，废弃本轮 candidate artifact并重新建立 source commit。
