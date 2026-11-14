# ADK 65 Skills 全量源码审查台账 · 2026-11-14

> **证据状态：source-only / design-review。** 只核冻结源码、Manifest 的 65 项身份/目录/描述和前述公开方法参照；不是 65 次真实模型执行、安全认证或 Token 实测。不可将“不修改”理解为“无缺陷”。外部资料仅提炼方法，不作为安装依赖。

- 冻结来源：`jiying2007/agent-dev-kit@879f962963512cb5be7b094b2a1bc85d4d8bf8e3`（此快照是 #261 待合并基线，不是未来 main）
- 本轮候选：`11.2.16`，11 个精准方法改进，54 项保留现有职责。
- 证据层级：E0/E1 源码/生产 Matcher/契约检查；E2–E4 模型、native host、HIL、安全运行或账单均 **not-measured**。
- 分工边界：唯一 Manifest / Runtime Router / 权限契约；不新增同义 Skill、工具调用后门、定时轮询、第三方自动安装与第二套 runtime authority。
- 参考方法：OpenAI skill-creator 的短入口/自由度；Anthropic skill-creator 的真实对照；Sentry skill-scanner / prompt-optimizer；Cloudflare audit 的范围/证据分层；Trail of Bits fp-check / post-patch；Zephyr 目标适配；NVIDIA SkillSpector 的供应链覆盖。仅只读研究。
- 任务目标：将不可信外部数据标为数据、不默认执行；不把模型/场景/设备不支持的命令当默认必执行；高风险维持原权限/独立验证/回滚要求。

| # | Manifest Skill | 来源 / 类别 | 决策 | 依据/拟改方向 | 冻结 Blob |
|---:|---|---|---|---|---|
| 1 | `adk-runtime-router` | core / routing | 保持本轮不变 | 保持唯一路由权威和按需加载 | `ce003460bbcc` |
| 2 | `adk-context-engineering` | core / routing | 保持本轮不变 | 保持唯一路由权威和按需加载 | `7bf14b57294f` |
| 3 | `adk-token-context-governance` | core / routing | 保持本轮不变 | 保持唯一路由权威和按需加载 | `47c0192048a8` |
| 4 | `adk-requirements-triage` | core / intake | 保持本轮不变 | 既有来源真实性/询问路由，等待行为对照 | `43e6e6e463d0` |
| 5 | `adk-structured-requirements-questioning` | core / intake | 保持本轮不变 | 既有来源真实性/询问路由，等待行为对照 | `b9328369a2cd` |
| 6 | `adk-repo-prompt-analysis` | core / intake | 保持本轮不变 | 既有来源真实性/询问路由，等待行为对照 | `8ae146546cb2` |
| 7 | `adk-skill-deep-analysis` | core / intake | 保持本轮不变 | 既有来源真实性/询问路由，等待行为对照 | `91cd8290d6cc` |
| 8 | `adk-lightweight-planning` | core / planning | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `fb572637a11c` |
| 9 | `adk-task-breakdown` | core / planning | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `7432c0c82fe9` |
| 10 | `adk-parallel-agent-governance` | core / planning | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `1ff0353145fe` |
| 11 | `adk-worktree-governance` | core / planning | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `aefb2fa3fd40` |
| 12 | `adk-context-compress-handoff` | core / planning | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `38f94ededa39` |
| 13 | `adk-interface-contract-design` | core / design | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `d93046c48ae4` |
| 14 | `adk-adr-writer` | core / design | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `6756ee1108c7` |
| 15 | `adk-component-api-stability` | core / design | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `0fd7c6917f0d` |
| 16 | `adk-register-map-design` | core / design | 改进（候选） | 示例寄存器不冒充真实芯片 | `c4ed08712d36` |
| 17 | `adk-bsp-analysis` | core / design | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `929e9ba760ad` |
| 18 | `adk-goal-authoring` | core / planning | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `f0a14b571e85` |
| 19 | `adk-planning-execution-loop` | core / planning | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `d15162b1e1c9` |
| 20 | `adk-driver-implementation` | core / implementation | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `e2a26df790d5` |
| 21 | `adk-driver-bringup-checklist` | core / implementation | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `7f5154f2926e` |
| 22 | `adk-bsp-porting-playbook` | core / implementation | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `c9a93413e3fb` |
| 23 | `adk-rtos-task-design` | core / implementation | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `bbb3c55aeda9` |
| 24 | `adk-interrupt-dma-patterns` | core / implementation | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `eb6d6b7ad74a` |
| 25 | `adk-protocol-stack-integration` | core / implementation | 改进（候选） | 设备适用性与抓包/故障注入权限 | `336c5ecaf6a3` |
| 26 | `adk-cmake-cross-build` | core / implementation | 改进（候选） | 交叉构建资源预算与权限 | `6c608d5fec24` |
| 27 | `adk-code-simplification` | core / implementation | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `875a68df6c74` |
| 28 | `adk-systematic-debugging` | core / debugging | 保持本轮不变 | 已具定向排障分工，本轮保持；真实环境待测 | `45bf02a8de90` |
| 29 | `adk-embedded-debug-transport` | core / debugging | 保持本轮不变 | 已具定向排障分工，本轮保持；真实环境待测 | `d4100591b2fa` |
| 30 | `adk-embedded-remote-debug-log-triage` | core / debugging | 保持本轮不变 | 已具定向排障分工，本轮保持；真实环境待测 | `9936e058634b` |
| 31 | `adk-offline-core-dump-triage` | core / debugging | 保持本轮不变 | 已具定向排障分工，本轮保持；真实环境待测 | `f9699a99f63b` |
| 32 | `adk-hardware-debugging` | core / debugging | 保持本轮不变 | 已具定向排障分工，本轮保持；真实环境待测 | `326cb28d44e7` |
| 33 | `adk-performance-profiling-embedded` | core / debugging | 改进（候选） | Linux/MCU 实测工具分支 | `c3e9ffe8d8ee` |
| 34 | `adk-test-strategy` | core / verification | 保持本轮不变 | 保留既有测试与完成门禁，本轮保持 | `9254d941d94d` |
| 35 | `adk-unit-test-embedded` | core / verification | 改进（候选） | host/SIL/HIL 证据分离 | `5a65324714a6` |
| 36 | `adk-integration-hil-sil` | core / verification | 保持本轮不变 | 保留既有测试与完成门禁，本轮保持 | `62402d43e311` |
| 37 | `adk-embedded-diagnostic-harness` | core / verification | 保持本轮不变 | 保留既有测试与完成门禁，本轮保持 | `664e510af7a1` |
| 38 | `adk-fault-injection-recovery` | core / verification | 保持本轮不变 | 保留既有测试与完成门禁，本轮保持 | `01ef6c409bdf` |
| 39 | `adk-artifact-gating` | core / verification | 保持本轮不变 | 保留既有测试与完成门禁，本轮保持 | `a5ef162658bf` |
| 40 | `adk-pilot-framework` | core / verification | 保持本轮不变 | 保留既有测试与完成门禁，本轮保持 | `63f375b6c0e1` |
| 41 | `adk-verification-before-completion` | core / verification | 保持本轮不变 | 保留既有测试与完成门禁，本轮保持 | `bacc35284785` |
| 42 | `adk-code-review-loop` | core / review_quality | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `1283f8667a27` |
| 43 | `adk-repo-drift-remediation` | core / review_quality | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `126165827f52` |
| 44 | `adk-static-analysis-c-cpp` | core / review_quality | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `68ac3dd358ed` |
| 45 | `adk-commit-pr-quality-gate` | core / review_quality | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `050cf95bc3c2` |
| 46 | `adk-release-versioning` | core / release_closure | 保持本轮不变 | 保留发布/现场证据与权威边界，本轮保持 | `cad0dc699b0d` |
| 47 | `adk-production-field-readiness` | core / release_closure | 保持本轮不变 | 保留发布/现场证据与权威边界，本轮保持 | `d864336f23a9` |
| 48 | `adk-embedded-release-orchestration` | core / release_closure | 保持本轮不变 | 保留发布/现场证据与权威边界，本轮保持 | `3aaa041a0484` |
| 49 | `adk-embedded-storage-layout-migration` | core / release_closure | 保持本轮不变 | 保留发布/现场证据与权威边界，本轮保持 | `2756aa6712a1` |
| 50 | `adk-cross-team-handoff` | core / release_closure | 保持本轮不变 | 保留发布/现场证据与权威边界，本轮保持 | `5e42ba9b906b` |
| 51 | `adk-branch-closeout` | core / release_closure | 保持本轮不变 | 保留发布/现场证据与权威边界，本轮保持 | `2d436fc51a76` |
| 52 | `adk-after-action-review` | core / release_closure | 保持本轮不变 | 保留发布/现场证据与权威边界，本轮保持 | `cec7d4b51daf` |
| 53 | `adk-memory-curator` | core / governance | 保持本轮不变 | 已有安全归档/知识责任边界，不增并行权威 | `5bc13c4f4174` |
| 54 | `adk-archive-governance` | core / governance | 保持本轮不变 | 已有安全归档/知识责任边界，不增并行权威 | `825237cd8d51` |
| 55 | `adk-knowledge-archive` | core / governance | 保持本轮不变 | 已有安全归档/知识责任边界，不增并行权威 | `73d851935005` |
| 56 | `adk-engineering-growth-review` | core / governance | 保持本轮不变 | 已有安全归档/知识责任边界，不增并行权威 | `06b4029aa40f` |
| 57 | `adk-external-practice-absorption` | optional / intake | 保持本轮不变 | 既有来源真实性/询问路由，等待行为对照 | `70b9c6153195` |
| 58 | `adk-data-fetch` | optional / implementation | 改进（候选） | 目标来源/凭证/只读权限与失败证据 | `0bf3f8dad22d` |
| 59 | `adk-email-imap-fetch` | optional / implementation | 改进（候选） | 目标来源/凭证/只读权限与失败证据 | `462e62009764` |
| 60 | `adk-fetch-url-content` | optional / implementation | 改进（候选） | 目标来源/凭证/只读权限与失败证据 | `31a1271eba44` |
| 61 | `adk-test-flakiness-triage` | optional / verification | 改进（候选） | 失败隔离/复测证据，不刷绿 | `f16b6c5dbd22` |
| 62 | `adk-security-supply-chain` | optional / review_quality | 改进（候选） | 只读研究与安装前审查分层 | `bc12847dcd0f` |
| 63 | `adk-prose-revision` | optional / review_quality | 保持本轮不变 | 已有用途及否定触发分工，未见需本轮改动的源级缺口 | `382ed9cdf9aa` |
| 64 | `adk-incident-rca-report` | optional / release_closure | 保持本轮不变 | 保留发布/现场证据与权威边界，本轮保持 | `1942cac37965` |
| 65 | `adk-skill-composition-governance` | optional / governance | 改进（候选） | 碰撞快路径与完整治理分流 | `380ef18726dd` |

## 本轮严格结论边界
1. `改进（候选）`：仅说明源文件方法修复将进入受保护 PR；完整 CI 与独立发布证据通过前不代表已落地主线。
2. `保持本轮不变`：代表已有相邻能力/权限和测试基础、避免无关改动；**不是**人工逐行安全认证、不等于 E2–E4 合格。
3. 同义/近义词不另建 Skill；无明确安全或任务失败证据不为每个 Skill 加“完整版”模板。质量/授权优先，Token/时延需真实模型与样本追踪验证。
4. 合并前检验所有路径来自 Manifest、无漏项、无新 identity、无复制外部代码；缺未知许可/设备/权限标 unknown / not-tested。源码优化必须保持已发布回归不退化。
