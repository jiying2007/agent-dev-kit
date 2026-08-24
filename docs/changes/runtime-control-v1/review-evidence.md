# Review Evidence：runtime-control-v1

- Review Target：三仓 working-tree whole-diff。
- Snapshot ID：root `0c1417a`；ADK `302378e`；Codex `f106de1`，叠加当前 working tree。
- Working Tree Overlay：全部目标变更均未 staged；review 对象是最新 working tree。
- latest_worktree_reviewed：true。
- Reviewer Independence：author-self-review；不冒充独立审查。
- Requirement Baseline：`requirements.md` R1-R10、`design.md` D1-D9。
- Mechanical Gate：working-tree pass；release-clean needs-fix。
- Spec Verdict：pass for implementation/source-to-live；release metadata pending owner commit。
- Quality Verdict：pass，blocker=0、major=0、minor=0 after fixes。

## Findings Closure

| Severity | Finding | Resolution | Verification |
|---|---|---|---|
| major | adapter 选择最近线程，可能在并发会话写错 Journal | 默认绑定 `CODEX_THREAD_ID`，支持 `--thread-id` | concurrent-thread unit test |
| major | 最新 checkpoint 后仍重复建议 checkpoint，apply 无法恢复 | 仅对缺失/落后 checkpoint 发出 warning | ADK deterministic unit test |
| minor | 旧 usage skill 空目录仍进入 managed state/live | 干净 build 并由 plan 删除三个目录 | live zero-residual scan |
| minor | 删除 skill 后 README profile 数量漂移 | 同步 37/69 并复验 | profile documentation test |

## Completion Guard

- build/test/smoke：pass；ADK 62/62，Codex 154/154，五 profile smoke。
- runtime：pass；source/build/target receipt 绑定，live `changed=0 stale=0 unmanaged=0`。
- security/privacy：pass；Journal 禁 raw prompt/messages/content/objective/cwd，wheel SHA fail closed。
- breaking：4.0.0 hard cut；无 alias、双读、双写、旧状态迁移。
- rollback：使用 apply plan 的备份恢复 live；源码回退需整体回退 Runtime Control change，不恢复旧双轨。
- release：needs-fix；真实 commit 前不刷新或伪造 `adk.lock` 与 release scorecard。
- prompt/UI/browser：not applicable；仅 CLI/engine/control-plane，runner smoke 已覆盖非仓 cwd、并发 thread、坏 wheel、失败退出码。
- permissions：未放宽 sandbox/approval/deny-path；Codex full gate 的 MCP deny-path 通过。
- trace eval：completion/gate manifests 复用现有 eval，Codex governance/full tests 通过；无新增模型或 prompt variant。
- Codify Decision：reusable_pattern=event-sourced single Engine；promotion_candidate=false，等待 owner review；next_task_friction_reduced=任务/Token/门禁只查一个 Journal/CLI；rollback_path=apply backup + whole-change revert；verification_evidence=`verification-evidence.md`。
