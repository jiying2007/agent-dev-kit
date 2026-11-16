# 65 个 Skill 的全量闭合清单

基线：`e13bd4788d5638c1eb34c169870f19dfd5285b6b`（11.3.6）。本轮读取全部 65 个注册入口、53 个随包参考资源，共 118 个路径；每个基线摘要均与实际 Git blob 内容重新核对。7 个 Skill 发生必要修改，58 个保留当前有效方法，没有新增或删除 Skill 身份。

这里的“保留”表示本轮完整源码检查未发现需要修改的具体缺口；它不是所有使用场景或原生 runtime 的认证。实际改动、方法合同、真实命令回归和最小上下文试用分别记录。完整逐文件 before/after SHA256 与字节数见 `evidence/portfolio-audit.json`。

## 逐项结论

| Skill | 处理 | 依据 |
|---|---|---|
| `adk-data-fetch` | 修改 | 修改候选 G4：父路由输出只声明 pass/needs-fix，两个子入口已有 partial，IMAP 另有 not-verified；应保留逐项成功/失败及未获取范围，不能把部分结果提升为完整或当空结果丢弃。 |
| `adk-email-imap-fetch` | 保留 | 保留：EXAMINE、UIDVALIDITY+UID、BODY.PEEK、MIME/附件边界、部分结果/逐项错误与有界重试明确；未接真实邮箱不宣称实际读取无副作用。 |
| `adk-fetch-url-content` | 保留 | 保留：HTTP(S)/origin/IP/redirect、robots/预算、正文类型/编码/base 链接、partial/空正文失败与数据不作指令边界已闭合。 |
| `adk-external-practice-absorption` | 保留 | 保留：固定来源/许可/独立 decision、scope 模式、同能力合并、七段证据与实际发布/source-to-live 权限边界，不导入外部执行器。 |
| `adk-incident-rca-report` | 保留 | 保留：事实/假设/已证实因果、未决根因及 5-Why 适用性清晰；只在事后报告，不自动恢复生产。 |
| `adk-prose-revision` | 保留 | 保留：report/revise 意图、事实/引文/代码/限定语保真、无问题保留与 no AI-author inference 具备，示例覆盖关键负例。 |
| `adk-security-supply-chain` | 保留 | 保留：source-only/preflight/runtime 三层适用性与 source-to-sink/coverage、真实安装工具边界完整；审查工具例只在核验目标和授权后适用。 |
| `adk-skill-composition-governance` | 保留 | 保留：collision-only/composition-change 分流、唯一 canonical matcher、真实行为/holdout/来源/成本/任务超时与采集失败分离；不另建评测器。 |
| `adk-test-flakiness-triage` | 保留 | Bounded sampler uses exact argv, fresh evidence and original exits; reports/statistical sample counts and conditional same-process order pollution separated. |
| `adk-adr-writer` | 保留 | 保留：lite/standard/deep 按实际风险选择，已覆盖建议与已批准状态、无可行备选、定向保真编辑及 reader-only 验收。 |
| `adk-after-action-review` | 保留 | 保留：普通 AAR 与晋级明确分离，三个随包 reference 可用；无可复用经验时可空候选，不假造成本或 owner approval。 |
| `adk-archive-governance` | 修改 | 修改 G5（静态设计反例）：未知 hash 差异仅重算摘要会丢失原完整性问题；明确保留旧/实测 hash 与当前内容，核可信原件及已批准变更后才重算，未知保持 needs-fix。没有真实归档事故或消费者运行证明。 |
| `adk-artifact-gating` | 保留 | 保留：状态与阶段分离、READY/PASS/NEEDS-FIX/BLOCKED 及签收/验证区别已闭合；direct reference 与现有 workflow 一致。 |
| `adk-branch-closeout` | 保留 | 保留：操作分流、同范围既有授权复用、精确 HEAD/checks、fresh-main、UNKNOWN 对账与删除单独授权完整。 |
| `adk-bsp-analysis` | 保留 | Target-family gate and bounded resource/call/history graph distinguish facts, inference and unknown; reference remains conditional. |
| `adk-bsp-porting-playbook` | 保留 | Verified target/config/toolchain variables, new output directory, make argv arrays and preserved failed build; device writes remain separate. |
| `adk-cmake-cross-build` | 修改 | CHANGE: real CMake 3.31.6 SKIP_RETURN_CODE test makes current published manual-build exit0 while every selected test is skipped; requires fresh result qualification. |
| `adk-code-review-loop` | 修改 | 修改候选 G2：主快照模板已修只读性，但 review-feedback-fixtures.md 保留旧命令；实际 Git mtime-only fixture 中 git status --short 改变 index 字节。合并重复命令到 canonical snapshot reference。 |
| `adk-code-simplification` | 保留 | 保留：公开边界测试、清理/副作用顺序、单模式修改及架构 seam 条件化；详细代码例已保留 cleanup，未发现新的可证行为回归。 |
| `adk-commit-pr-quality-gate` | 保留 | 保留：message-only/PR-readiness/high-risk 适用性已分开，同身份有效回执复用与专项风险无放宽。 |
| `adk-component-api-stability` | 保留 | Distinguishes source API, binary ABI and behavior; preserves old consumer bytes, type-information limitations and raw failure statuses. |
| `adk-context-compress-handoff` | 保留 | 保留：默认随入口自包含模板、已知源码根才可选内部 attestation；raw pointer、权限、fallback、最多三个动作明确。 |
| `adk-context-engineering` | 保留 | 保留：stable/task/evidence/on-demand 分层、权限与恢复模板随包自包含；已有 11.3.6 导出消费者回归覆盖源码 helper 缺失。 |
| `adk-cross-team-handoff` | 保留 | 保留：lite/formal、pending/accepted、接收方 cold read 与真实签收分离，未执行权限转移/设备恢复不声称完成。 |
| `adk-driver-bringup-checklist` | 保留 | Stages minimal/functional/soak/production separately; actively probing and read-side-effect registers are not mislabeled passive. |
| `adk-driver-implementation` | 保留 | Linux/RTOS/bare-metal primitives and lifetime/error/cancel/late-completion cases are target-specific; host evidence not conflated with hardware. |
| `adk-embedded-debug-transport` | 保留 | Multiple available channels compared with actual effects; attach/halt/continue separated from passive existing-state reads. |
| `adk-embedded-diagnostic-harness` | 保留 | Expected return/invoke_ret matrix separates harness errors, product failures and environment dependencies; missing HIL not silently passed. |
| `adk-embedded-release-orchestration` | 保留 | Prepare/publish/flash identities and receipts remain separate; multi-MCU partial success/recovery linked conditionally. |
| `adk-embedded-remote-debug-log-triage` | 保留 | Layered reachability and ADB semantic checks avoid ping/exitcode shortcuts; breaker, recovered identity and HIL expansion retain evidence. |
| `adk-embedded-storage-layout-migration` | 保留 | Data-preservation/config-chain/host-dry-run checks distinguish content update versus layout change; real pilot receipt required before batch handoff. |
| `adk-engineering-growth-review` | 修改 | 修改候选 G3：frontmatter 与 README 仍允许默认跨项目宽读，正文/reference 却要求 index-first/用户明确跨项目授权；统一为已授权范围优先，减少无关读取。 |
| `adk-fault-injection-recovery` | 保留 | Risk-selected failure models, authorized isolated target, bounded exposure and recovery receipts; no unrequested production load or universal fault-count threshold. |
| `adk-goal-authoring` | 保留 | 保留：继续执行非触发、原验收分母/依赖/batch 保留，resume 只读边界与示例 JSON 一致；不改宿主预算。 |
| `adk-hardware-debugging` | 保留 | Runtime-to-link address mapping, matched ELF, fault-register capability and confidence boundaries prevent symbol or MCU-family overclaims. |
| `adk-integration-hil-sil` | 修改 | CHANGE: published CTest exit0 is not execution qualification when SKIP_RETURN_CODE makes all tests skip; add self-contained fresh JUnit evidence and explicit qualification. |
| `adk-interface-contract-design` | 保留 | Directed version/capability check, independent caller-visible contract, effect/lifecycle recovery and bidirectional evidence are explicit; no blind downgrade. |
| `adk-interrupt-dma-patterns` | 保留 | CPU/device buffer ownership, cache direction, teardown and ISR budgets are target-specific; additional observation reference correctly separates IRQ from thread latency. |
| `adk-knowledge-archive` | 保留 | 保留：新候选与归档修复分离，证据/source/topic/脱敏/路径未知阻塞及长期规则不自动晋升清楚。 |
| `adk-lightweight-planning` | 保留 | 保留：用户只要计划时只读、必要步骤数量与可核验信号、可逆假设和阻塞未知分开，不转成额外执行。 |
| `adk-memory-curator` | 保留 | 保留：report-only、证据/冲突/晋级边界完整，secret 查询只列文件名，覆盖限制已明示。 |
| `adk-offline-core-dump-triage` | 保留 | Matched artifacts/libs and safe auto-loading precede offline backtrace; missing symbols/frames stay partial. |
| `adk-parallel-agent-governance` | 修改 | 修改候选 G1：实际两种 core export 均不含 templates/planning/worker-contract.md，而入口与 reference 无条件要求；改默认使用实际已随包的工作包并条件化源码 helper。 |
| `adk-performance-profiling-embedded` | 保留 | Low-overhead diagnosis, equivalent-workload A/B and tool perturbation boundaries retained; Massif/heap versus Memcheck/leaks and observed stack margin versus upper bound differentiated. |
| `adk-pilot-framework` | 保留 | 保留：任务验收与健康检查分开，smoke/收益比较分开，失败/环境阻塞/不确定不混同，来源指针与部署边界明确。 |
| `adk-planning-execution-loop` | 保留 | 保留：复用原 Goal/state/evidence、inline fast path、同失败停止取证和中断副作用对账已覆盖实际续做，未发现新功能缺口。 |
| `adk-production-field-readiness` | 保留 | Readiness requires target hardware/artifact and actual factory/OTA/recovery evidence; pilot measurement not treated as production qualification. |
| `adk-protocol-stack-integration` | 保留 | Offline versus active capture and protocol layer evidence separated; remaining deadline includes attempts/backoff and non-idempotent unknown-result reconciliation. |
| `adk-register-map-design` | 保留 | Actual datasheet/errata semantics, reserved/W1C/read-clear behavior and conceptual SVD example are clearly distinguished. |
| `adk-release-versioning` | 保留 | 保留：按真实发布 baseline 收集完整历史、shallow/无效祖先失败、SemVer/immutable tag/发布权限边界一致。 |
| `adk-repo-drift-remediation` | 保留 | 保留：issue-map 先行、共享触点单 owner、源根限定命令、原用户 dirty 保留、remaining risk 必须交代。 |
| `adk-repo-prompt-analysis` | 保留 | 保留：repo@commit 与真实 callsite/role/trust boundary、只读方法吸收、无宿主 trace 不声称效果，索引优先。 |
| `adk-requirements-triage` | 保留 | 保留：brief/execution-handoff/high-risk 区分、已有批准任务不重访谈、可执行字段与风险适用性清楚。 |
| `adk-rtos-task-design` | 保留 | Fixed-priority recurrence and illustrative arithmetic checked; model assumptions, ISR interference, blocking and observed WCET limits explicit. |
| `adk-runtime-router` | 保留 | 保留：可信 inventory、唯一 primary、optional-installed 边界、版本适配与用户拒绝、失败和 evidence depth 均已覆盖；不新增第二路由权威。 |
| `adk-skill-deep-analysis` | 保留 | 保留：source-discovery 有界核源、method-only/deep/behavior 分离、最小实施交接可直接用于当前优化；不把候选发现计作验证或自动安装。 |
| `adk-static-analysis-c-cpp` | 保留 | TU/changed-header dependency coverage and compile database identity preserved; empty scans not passed, nonzero parser/tool outcomes not swallowed. |
| `adk-structured-requirements-questioning` | 保留 | 保留：Explore/Challenge、稳定问题 ID/依赖/部分回答/上游失效、用户退出与已明确直接做的路径已具备。 |
| `adk-systematic-debugging` | 保留 | 保留：最小红信号、单变量、Repair Note、Sanitizer 真实报告/exit0 边界与领域取证分流已覆盖；不据缺现场证据伪造根因。 |
| `adk-task-breakdown` | 保留 | 保留：纵向切片/expand-migrate-contract、依赖 frontier、owner/write scope、机器 v2 条件化；实际示例保留旧消费者并拒绝过早移除。 |
| `adk-test-strategy` | 保留 | 保留：Level0/1/2 适用性、独立 expected/错误变体、checker 校准、资源隔离、真实行为与静态证据分开。 |
| `adk-token-context-governance` | 保留 | 保留：balanced/high-risk 原文回退、动态内容分层、真实用量归因与未测量边界完整，不通过加字节预算掩盖噪音。 |
| `adk-unit-test-embedded` | 保留 | Contract-derived observable assertions and independent bounded stateful oracle retained; host/compile/emulator/HIL limits explicit. |
| `adk-verification-before-completion` | 保留 | 保留：checkpoint/goal-final 分离、同身份命令/证据新鲜度与独立 reviewer、条件性 checker 校准和生命周期门禁清楚。 |
| `adk-worktree-governance` | 保留 | 保留：无隔离价值时 stay-current、用户 dirty 不动、来源与 shared resource、cleanup 独立授权及最终主线验证一致。 |

## 后续验证边界

- 并行/Review 通过真实消费端导出与 Git index 不变性回归；父子状态、成长读取范围和归档异常最初是静态合同缺口，另以一轮最小上下文任务产物观察其可用性。
- CMake 的 all-skipped 与超时后代问题来自真实工具反例；all-disabled false-pass 假设被实际 exit 8 反驳，失败和无效 fixture 原始记录保留。
- 8 个 profile 原上限不变；当前源字节与最终 CI/Release 状态分别由 measurement/verification 和平台真实回执给出。
