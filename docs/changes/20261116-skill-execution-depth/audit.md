# 65 个 Skills 全量审计与本轮落地

基线：`5f442723e95fa7ca846b7c3ddc9f9995c7a27065`（11.3.7）；候选：11.3.8。

读取覆盖 56 个 core、9 个 optional 入口。三个分组实际读取 144 个互斥文件，根集成补读 7 个许可证与 1 个 OpenAI 元数据文件；与基线 Git tree 核对全部 152 个受版本控制的 Skill 文件，逐文件 SHA256、大小与 Git blob 一致。其中 65 个入口、53 个 reference；没有缺项。新增 transport reference 计入候选，未冒充基线读取。

最终 8 个 Skill 增强，57 个保留；全部 Skill 目录合计源码字节变化 `-92 B`。8 个原有 profile 容量门槛全部通过，阈值未改。源码字节不是实际上下文或模型费用指标。

## 8 个实际修复

| Skill | 方法与验收 | 源码字节变化 |
|---|---|---:|
| `adk-worktree-governance` | 与 canonical Review 保持只读 preflight 语义，执行隔离 index 不变验证。 | +192 B |
| `adk-register-map-design` | 区分 undefined、unknown 和条件性 reset，仅比较适用且可安全读取的已知位；明确全括号 C 比较式。 | -64 B |
| `adk-protocol-stack-integration` | 按实际传输拆分 stream 分帧/短读/合帧、datagram 空消息与截断；保留部分写偏移、限长和剩余 deadline。 | +381 B |
| `adk-performance-profiling-embedded` | 核实际运行二进制/共享库与 dispatch 身份；映射、磁盘文件和实际分支执行证据分开。 | -104 B |
| `adk-code-review-loop` | 在原始差异中禁 external diff/textconv、FSMonitor、相对路径/颜色和 gitlink 隐藏；保留目标、base、dirty、index 与补充语义视图边界。 | -565 B |
| `adk-repo-drift-remediation` | 防止本地 FSMonitor 配置触发 helper，且不让只读漂移检查刷新 index。 | +109 B |
| `adk-branch-closeout` | 关闭 preflight 的 FSMonitor 与可选 index 写入；完整保留未跟踪和子模块状态。 | +93 B |
| `adk-test-flakiness-triage` | 仅对已证实 readiness 竞争引入原生条件等待，保留操作身份、合法零值、取消及单调截止预算。 | -134 B |

## 逐项决定

| Skill | 决定 | 依据 |
|---|---|---|
| `adk-runtime-router` | 保留 | 唯一 primary、可信 inventory、optional 安装证据、版本适配/弃权与已批准执行意图都有独立边界。 |
| `adk-context-engineering` | 保留 | 稳定规则与动态证据分开、按需工具与最小上下文、自包含恢复模板及来源缺失边界明确。 |
| `adk-token-context-governance` | 保留 | 分层读取与 raw fallback、实际用量归因、源码字节和真实 token 分开；不用扩大预算掩盖噪声。 |
| `adk-requirements-triage` | 保留 | brief/execution/high-risk 的必要输入有区别，既有明确计划不重访谈、不编造路径或结果。 |
| `adk-structured-requirements-questioning` | 保留 | Explore 一问与 Challenge 依赖 frontier、部分回答/修订、用户退出及静态/真实效果边界清楚。 |
| `adk-repo-prompt-analysis` | 保留 | source identity、调用链和 role/trust-boundary 分开，索引优先、不执行来源脚本、不默认长报告。 |
| `adk-skill-deep-analysis` | 保留 | 有界一手发现、method/deep/behavior 分流、既有能力净增益和可实施交接明确，不声称穷尽全网或原生效果。 |
| `adk-lightweight-planning` | 保留 | 只读计划与真正执行明确分流，按可观察验收和必要未知项给最少动作，无额外模型轮次。 |
| `adk-task-breakdown` | 保留 | 纵向切片、必要迁移例外、真实 DAG/权限/写冲突及按需机器合同清楚；独立消费者迁移示例保留。 |
| `adk-parallel-agent-governance` | 保留 | 先判断并行收益、唯一写 owner、完整随包任务合同与来源保留，最终集成不由子项 DONE 代替。 |
| `adk-worktree-governance` | 增强 | 与 canonical Review 保持只读 preflight 语义，执行隔离 index 不变验证。 |
| `adk-context-compress-handoff` | 保留 | 自包含交接模板、仅可选源码辅助、最多三动作和权限/证据/fallback 已有；保留。 |
| `adk-interface-contract-design` | 保留 | 版本/能力方向、状态资源生命周期、实际副作用、schema 与双向规格核对明确；示例不扩大到 ABI/wire 认证。 |
| `adk-adr-writer` | 保留 | 按风险区分 lite/standard/deep，保留 proposed/accepted、实际备选与读者验收；没有必须新增的执行缺口。 |
| `adk-component-api-stability` | 保留 | Separate old-source/new-header build, old object/executable ABI behavior, symbol-only limits and abidiff exit semantics; no verified new gap. |
| `adk-register-map-design` | 增强 | 区分 undefined、unknown 和条件性 reset，仅比较适用且可安全读取的已知位；明确全括号 C 比较式。 |
| `adk-bsp-analysis` | 保留 | Target-family branches, scoped resource/history tracing, authoritative hardware sections and confirmed/inferred/unknown boundaries remain adequate; no verified new gap. |
| `adk-goal-authoring` | 保留 | 既有 Goal 执行不重建合同，保留原验收/依赖/批次及有界只读 resume；当前方法无新缺口。 |
| `adk-planning-execution-loop` | 保留 | 恢复原验收与有效回执、inline 实施路径、部分阻塞独立 READY 继续和未知副作用对账齐全。 |
| `adk-driver-implementation` | 保留 | Runtime-specific lifecycle, ownership, cancellation and late completion paths are explicit; host/build evidence does not claim hardware validation. |
| `adk-driver-bringup-checklist` | 保留 | Stage-specific minimal/functional/soak/production evidence, active-probe and read-side-effect distinctions prevent unrelated stage or permission escalation. |
| `adk-bsp-porting-playbook` | 保留 | Reviewed target-derived Kbuild argv, new output directory, compiler/ABI identity, existing-config preservation, resource budgets and independent device handoff; no verified new gap. |
| `adk-rtos-task-design` | 保留 | Response-time recurrence and example arithmetic, model assumptions, ISR/blocking and measured-maximum versus WCET limits are coherent. |
| `adk-interrupt-dma-patterns` | 保留 | Platform-specific buffer ownership/cache ordering, bounded ISR, late completion and teardown evidence remain explicit; both references were read. |
| `adk-protocol-stack-integration` | 增强 | 按实际传输拆分 stream 分帧/短读/合帧、datagram 空消息与截断；保留部分写偏移、限长和剩余 deadline。 |
| `adk-cmake-cross-build` | 保留 | Preset/manual paths, actual binaryDir/configuration, compile-only and fresh CTest JUnit qualification cover previous failures; process timeout investigation remains with root integrator. |
| `adk-code-simplification` | 保留 | 先固定公开行为、一次一种模式、保留清理/副作用与用户改动；示例与单次变更范围匹配。 |
| `adk-systematic-debugging` | 保留 | 最小红信号、单变量、负结果、无增量停止及 target-specific sanitizer 判读已有；不虚构假设。 |
| `adk-embedded-debug-transport` | 保留 | Channel availability, effect classification, attach/halt/continue and recovery boundaries are explicit; no verified new gap. |
| `adk-embedded-remote-debug-log-triage` | 保留 | Layered route/transport/shell/app status, ADB semantic checks, circuit breaker and fresh post-recovery identities remain applicable. |
| `adk-offline-core-dump-triage` | 保留 | Artifact/BuildID association, target sysroot, disabled auto-loading, missing-library/frame limits and likely-root-cause separation are explicit. |
| `adk-hardware-debugging` | 保留 | Matched module/kernel/ELF, runtime-to-link mapping and Cortex-M-specific register availability avoid invalid symbol/hardware conclusions. |
| `adk-performance-profiling-embedded` | 增强 | 核实际运行二进制/共享库与 dispatch 身份；映射、磁盘文件和实际分支执行证据分开。 |
| `adk-test-strategy` | 保留 | Level0/1/2 真实风险分层、公开 seam/独立 expected/checker 校准和并行资源隔离清楚；保留。 |
| `adk-unit-test-embedded` | 保留 | Independent contract oracle, bounded stateful examples, useful negative paths and host/compile/HIL boundaries remain; external research may separately propose mutation triage. |
| `adk-integration-hil-sil` | 保留 | Fresh report qualification, required test identities, shared-rig isolation, actual device hash and final health are explicit; no verified new gap. |
| `adk-embedded-diagnostic-harness` | 保留 | Expected code/invoke_ret matrix and product/harness/environment failure classification remain useful; real tools and device evidence remain conditional. |
| `adk-fault-injection-recovery` | 保留 | Risk-selected failure models, bounded authorized isolated injection, actual recovery receipts and relevant watchdog qualification remain intact. |
| `adk-artifact-gating` | 保留 | 计划 READY 与测试/审阅 PASS 及真实签收分开，适用消费者和已有流程清楚；保留。 |
| `adk-pilot-framework` | 保留 | 任务产物验收与环境健康分开，smoke 不证明稳定性或收益，失败/blocked/inconclusive 有区别。 |
| `adk-verification-before-completion` | 保留 | checkpoint 与 goal-final、适用性矩阵、checker 负例、真实权限/独立证据与资格边界保留。 |
| `adk-code-review-loop` | 增强 | 在原始差异中禁 external diff/textconv、FSMonitor、相对路径/颜色和 gitlink 隐藏；保留目标、base、dirty、index 与补充语义视图边界。 |
| `adk-repo-drift-remediation` | 增强 | 防止本地 FSMonitor 配置触发 helper，且不让只读漂移检查刷新 index。 |
| `adk-static-analysis-c-cpp` | 保留 | Target compile database/TU coverage, changed-header dependency fallback, empty TU failure and actual analyzer exit propagation remain explicit. |
| `adk-commit-pr-quality-gate` | 保留 | message-only、PR-readiness 与专项风险按适用性分流，复用同快照有效证据，未放宽真实门禁。 |
| `adk-release-versioning` | 保留 | 实际发布基线与完整历史、shallow/非祖先拒绝、未知类型/revert 不丢弃及发布权限分开。 |
| `adk-production-field-readiness` | 保留 | Factory/OTA/rollback/diagnostics and hardware-dependent readiness are separated from build/pilot claims; no verified new gap. |
| `adk-embedded-release-orchestration` | 保留 | Preparation/publication/device write identities and receipts are separate; multi-MCU staged/activation/health/rollback paths already account for partial success. |
| `adk-embedded-storage-layout-migration` | 保留 | Layout/content update routing, preserved data, config/build/artifact chain and actual pilot receipt are separated from host dry-run. |
| `adk-cross-team-handoff` | 保留 | lite/formal 区分、真实接收方/权限/签收不由文档替代，cold-read 按需；保留。 |
| `adk-branch-closeout` | 增强 | 关闭 preflight 的 FSMonitor 与可选 index 写入；完整保留未跟踪和子模块状态。 |
| `adk-after-action-review` | 保留 | 普通复盘与长期晋级分开，随包参考及空候选允许；不把未观测成本或 owner 决定编造为结果。 |
| `adk-memory-curator` | 保留 | report-only、作用域/冲突/证据/脱敏边界明确；秘密扫描只列文件名且标覆盖限制。 |
| `adk-archive-governance` | 保留 | 未知摘要差异保留旧值和当前内容，实际授权/可信原件确认后才重算；现有修复范围与入口可用。 |
| `adk-knowledge-archive` | 保留 | 新候选与已有归档修复分开，保留来源/脱敏/实际目的地与规则晋级边界；保留。 |
| `adk-engineering-growth-review` | 保留 | 入口/README/reference 的已授权范围与 index-first 一致，建议有观察与可检查信号，不扩大外发或读取范围。 |
| `adk-external-practice-absorption` | 保留 | Execution modes and source-root-qualified command examples already addressed latest prior defects; preserve separate source/owner/implementation evidence. |
| `adk-data-fetch` | 保留 | Parent mapping preserves pass/partial/not-verified/needs-fix and explicitly requires selected child installation; protects incomplete output and least access. |
| `adk-email-imap-fetch` | 保留 | EXAMINE and BODY.PEEK, mailbox/UIDVALIDITY/UID, budgets, MIME and partial results are explicit; no source-confirmed missing step requiring another rule. |
| `adk-fetch-url-content` | 保留 | Origin/IP/redirect checks, byte/time limits, main-text extraction, relative URLs, untrusted content and partial states are already explicit. |
| `adk-test-flakiness-triage` | 增强 | 仅对已证实 readiness 竞争引入原生条件等待，保留操作身份、合法零值、取消及单调截止预算。 |
| `adk-security-supply-chain` | 保留 | Three review scopes, source-to-sink, inspected/omitted/unavailable and no static safety certification already incorporate useful external practices. |
| `adk-prose-revision` | 保留 | Report/revise split, fact/literal preservation, no-edit outcome and eight counterexamples match current user constraints. |
| `adk-incident-rca-report` | 保留 | Stable-incident scope, confirmed/hypothesis/unresolved chain and concise default avoid ritual 5-Why and invented accountability. |
| `adk-skill-composition-governance` | 保留 | Collision-only fast path, unique primary, existing matcher/effect_trials, frozen holdout, invalid evaluation and outcome/overhead separation are already unusually complete. |

## 可检查证据

- `evidence/portfolio-audit.json`：152 个基线读取身份、65 个决定和候选源码体积。
- `evidence/raw-observations.json`：原始反例、无效夹具、RED/GREEN、真实 socketpair、分组报告及历史 CTest 超时摘录；UTF-8 原文可无损还原并核摘要。
- `evidence/profile-first-check.json` 与 `profile-final.json`：初次容量拒绝及最终原门槛通过。
- `evidence/cmake-baseline.json`：补齐工具后实际运行 5 个 CMake/Ninja 用例；历史 CI 超时根因仍未知。
- `evidence/consumer-task.md` 与 `consumer-response.json`：独立新会话对 3 个工程案例的实际输出。只读 6 个输入；performance 入口在读取期间被压缩，其后因独立审查又调整版本及 protocol 的独立状态机约束。响应保留各次读取哈希，已在同一会话重读最终版本并更新意见。它不是盲测、独立重复 A/B 或宿主认证。
- `source-review.md` 与 `evidence/research-sources.json`：10 个外部仓库、15 个具体一手文件及固定 commit/blob、许可检查层级和采用/拒绝原因。

原始观察的代码身份与最终完整回归分别记录；任何中间失败不通过修改原记录抹去。
