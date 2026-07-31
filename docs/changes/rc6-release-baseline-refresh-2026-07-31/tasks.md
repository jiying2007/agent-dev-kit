# 任务：RC6 release baseline refresh

- [x] T1 建立 RC6 版本、migration 和 M5 campaign contract；verify：strict、release check、Software M5 ready tests。
- [x] T2 在 Python 3.11/3.12 local-CI 环境完成全回归和安全门禁；verify：两套支持环境结果均 pass。
- [ ] T3 提交 release source，并从 exact commit 双构建一致 artifact；verify：`cmp`、SHA256、checksum、source file count。
- [ ] T4 执行 RC5 到 RC6 rehearsal；verify：升级、candidate rollback、RC5 managed hash restore 全 pass。
- [ ] T5 固化 ADK evidence commit；verify：release source 到 evidence commit 的 mapped path diff 为空。
- [ ] T6 更新根仓 policy/evidence/current-status/scorecard/ledger/gitlink；verify：current-status consistency pass。
- [ ] T7 运行根仓 full gate、final-ready、提交和推送；verify：full 60/60、两个远端 HEAD 与本地一致。

## Ownership 与并行冲突检查

- owner：leiwenjun；implementer：Codex 当前会话。
- scope_write：ADK 版本与 release change 工件；根仓 release policy/evidence/status/scorecard/ledger/gitlink。
- scope_read：RC5 artifact、release implementation、历史 release evidence、Knowledge Hub provisional validation。
- must_not_touch：根仓已登记的 dirty reference worktrees、缓存与未登记独立仓库，Codex source/live 目录、tag、remote release 和凭证。
- shared contract：版本、artifact、rehearsal、root policy 串行执行，不并行写入。
- blocking condition：支持 Python 容器不可用、RC5 artifact checksum 失败、artifact 不可复现、rehearsal 失败两次或需要 live/remote 新授权。
- output contract：exact hashes、rehearsal JSON、Evidence Index、full gate 结果与明确 source-to-live pending 状态。

## 轻量工件与收敛结论

- planning：`proposal.md`、`design.md`、本文件、`state.yaml`。
- evidence：`negative-results.md`、`release-rehearsal.json`、`verify-report.md`。
- completion claim：仅声明 RC6 source/local release baseline 可复核；不声明 live applied、runtime certified、M5 certified 或 final release ready。
