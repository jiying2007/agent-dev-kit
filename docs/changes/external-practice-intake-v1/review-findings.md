# Review Findings：external-practice-intake-v1

## 当前结论

- Review pass：implementation/release source 与 root integration 无未闭环 blocker 或 major。
- Completion gate：本地 source、RC4 release rehearsal、root quick/full、legacy residue 和 Knowledge Hub candidate 均有证据；完成声明仅限本地 source 终态，不扩展为 live/remote/field/M5 certified。
- Reviewer responsibility：Codex 分离实现阶段与复审阶段执行；最终 owner/合并责任仍为 `leiwenjun`。

## Findings 与闭环

| ID | Severity | Finding | Resolution | Verification |
|---|---|---|---|---|
| CR-01 | major | input/output symlink 在 resolve 后检查会漏掉链路 | 先逐层拒绝 symlink，再做 containment | symlink input/output 负例 |
| CR-02 | major | evidence/queue 只做浅层检查且未绑定 ledger | 精确校验 jobs/boundaries/count/as_of/SHA | inconsistent evidence/queue、queue binding 负例 |
| CR-03 | major | 多输出 cycle/registration 可能部分写入 | multi-file transaction、备份与失败回滚 | forced failure/no-partial-write 负例 |
| CR-04 | major | provider 不适用字段可能被静默忽略 | provider-specific exact field set | ignored-provider-argument 负例 |
| CR-05 | major | 微信任意 verification status 可能被误信 | policy 显式 bounded trusted allowlist | unverified WeChat 负例 |
| CR-06 | major | reference apply 未绑定 clean local Git source/origin/HEAD | apply 前精确核验 clean、HTTPS origin、fixed HEAD | isolated apply/rollback rehearsal |
| CR-07 | major | registration metadata 与 submodule 可能非事务且目标层错误 | registry/matrix/lifecycle/applied-plan 同事务；target 固定 `llm_agent` | forced transaction rollback |
| CR-08 | major | removal plan 使用旧 OSS schema、未哈希证据且可能暗示 destructive apply | `reference-repository-removal/v1`、artifact SHA、dry-run-only；`--apply` 拒绝 | removal positive/negative tests |
| CR-09 | major | profile 引用治理 Agent 但遗漏默认 Skill | 补齐 lifecycle 排序的 interface/ADR/test/security/commit Skills | profile coherence/runtime routing/taxonomy |
| CR-10 | major | 旧 Skill 删除令 file-mode/security inventory 把预期删除误判为内容风险 | live Git inventory 跳过缺失内容；显式 inventory 仍 fail closed | file-mode missing inventory 负例、security pass |
| CR-11 | minor | `practice_intake.py` 与 `reference_repository.py` 体积较大 | 当前按单 CLI 合同保持内聚；provider/transaction/schema 边界均为独立函数且有端到端测试 | AST/ShellCheck/full tests；后续仅在新增 provider 时评估拆包 |

## 配置与兼容决策

- Config drift：manifest 增加 curator Agent、research-intake profile closure、一个 optional Skill、一个 Workflow 和 RC4 campaign contract；默认 profile 不自动安装 optional Skill。
- Skill intake：`adk-external-practice-absorption` 为 `global-ready / optional`；不进入 core，不为每个 provider 创建独立 Skill。
- Breaking change：`adk-intake-workflow` 与旧 OSS/WeChat intake CLI/schema 硬删除，无 alias、wrapper、双写或自动迁移。
- Rollback：恢复 checksum-verified 完整 RC3 artifact/commit；不得把旧资产重新塞回 RC4。
- Release boundary：local exact-commit build/rehearsal pass；live apply、remote CI、push/tag/publish 仍需独立授权/证据。

## Completion Gate

- blocker：0。
- major：0（CR-01–CR-10 全部修复并复验）。
- minor：1（CR-11，非阻塞维护建议）。
- 结论：`review-passed / local-terminal-source-pass / external-boundaries-explicit`。
