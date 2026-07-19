# 执行任务：external-practice-intake-v1

- [x] T1 需求、边界、API 证据与破坏性迁移清单冻结；verify：proposal/design/tasks 完整且旧入口调用点已检索
- [x] T2 增加统一 source policy、candidate/decision/cycle schema 与正负 fixtures；verify：新 checker 对每类合同 fail closed
- [x] T3 实现 `tools.codex_assets.practice_intake` 与唯一 shell wrapper；verify：七类 provider、幂等、redaction、budget、degraded、symlink 与事务行为测试通过
- [x] T4 增加 curator Agent、optional absorption Skill 与 Workflow，并删除前代 intake skill；verify：manifest sync、catalog、routing/metadata 测试通过
- [x] T5 硬切根调用方、repository onboarding handoff、文档与门禁，删除旧脚本/manifest/fixtures/tests；verify：active-tree legacy audit 零命中，历史 provenance 不被重写
- [x] T6 完成定向、root quick/full、ADK strict/quick/full、安全、性能和非仓库 cwd smoke；verify：Evidence Index 记录真实退出码与报告路径
- [x] T7 独立 review 修复闭环、状态一致性、Knowledge Hub reviewing candidate 和复盘；verify：blocker=0、major=0，完成声明与证据一致

## Ownership 与并行冲突检查

- scope_write：根仓 external-practice manifest/schema/tool/wrapper/fixtures/tests/check、活跃 intake/absorption docs、repository onboarding handoff；ADK change 工件、curator Agent、optional Skill、Workflow、manifest/profile/catalog/docs/tests。
- scope_read：根/ADK AGENTS、旧 OSS/WeChat/official implementation、全部调用点、官方 GitHub/GitLab/Gitee API 文档、Hub decision 候选。
- must_not_touch：既有 dirty 参考子仓、未跟踪研究目录、历史 reports/adoption provenance、远端、`~/codex`、`~/.codex`、Knowledge Hub active/memory。
- 并行冲突：共享 schema、root scripts、ADK manifest/profile 均串行；本轮不派生子 Agent。

## 长任务防卡死

- retry_budget：同一根因最多 2 次；第三次前必须 replan 或 split。
- staleness_threshold：45 分钟或每完成一个 T 项更新一次 change 证据。
- heartbeat：每阶段至少新增一条测试、负结果或状态证据。
- stop_condition：`pass | replan | split | blocked | abort`。
- completion_claim：只有 T1–T7 和 completion gate 均有证据时，才能声明统一 intake 硬切完成。
- verifier：`adk-verification-before-completion` 与机械门禁；claimant 不能以 fixture 替代 live 网络声明。

## 轻量工件与收敛结论

- requirements：`proposal.md`。
- design：`design.md` 与根 `architecture/external-practice-intake-terminal.md`。
- task checklist：本文件。
- execution evidence：`negative-results.md`、后续 `verification-evidence.md`、`review-findings.md`、`verify-report.md`。
- 收敛结论：`local-terminal-source-pass / external-boundaries-explicit`；T1–T7、独立复审和本地 release rehearsal 已闭环，source-to-live、remote CI/publish、runtime campaign 与 field/M5 certification 仍由独立权限和外部证据门禁控制。
