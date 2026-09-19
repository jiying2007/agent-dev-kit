# Skill Routing Matrix

- source: manifest.json:routing + skill_routing_matrix

## Skill Routing Matrix

| Scenario | Description | Availability | Profiles | Workflow | Primary | Supporting | Fallback | Mutually Exclusive | Positive Example | Negative Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `runtime_routing` | 任务开始前选择 profile、primary skill 和 supporting skill | profile-resolved | core, embedded-fullstack | `runtime-routing` | `adk-runtime-router` | - | adk-requirements-triage | - | 判断这个任务应该使用哪个技能 | 只要计划，不要修改文件 |
| `unclear_requirement` | 需求、边界、验收或优先级不清，需要先收敛 | profile-resolved | core, embedded-fullstack | `feature-delivery` | `adk-requirements-triage` | - | - | adk-lightweight-planning, adk-planning-execution-loop | 需求不清楚，先梳理目标和验收标准 | 按已有计划直接执行 |
| `planning_only` | 用户明确要求只读计划，不创建、不修改、不删除文件 | profile-resolved | core | `-` | `adk-lightweight-planning` | - | adk-requirements-triage | adk-planning-execution-loop | 先给计划，不要改文件 | 按计划执行并修改代码 |
| `task_breakdown` | 需求已明确但任务过大，需要拆成可执行任务包 | profile-resolved | core, embedded-fullstack | `feature-delivery` | `adk-task-breakdown` | adk-requirements-triage | adk-lightweight-planning | - | 任务太大，拆解成任务包 | 根因不明，先定位问题 |
| `long_execution` | 长任务需要计划审查、检查点、恢复和完成前闭环 | optional-skill-required | core, embedded-fullstack | `feature-delivery` | `adk-planning-execution-loop` | adk-verification-before-completion | adk-lightweight-planning | adk-lightweight-planning | 分阶段执行并持续验证 | 只要计划，不要执行 |
| `unknown_root_cause_bug` | 行为异常但根因未明，需要系统化定位再修复 | profile-resolved | core, embedded-fullstack | `bugfix-delivery` | `adk-systematic-debugging` | - | - | adk-lightweight-planning | 问题根因不明确，需要定位后修复 | 新功能需求需要先拆解 |
| `embedded_log_analysis` | 嵌入式串口、boot、dmesg、ADB/logcat、OTA 或现场日志分析 | profile-resolved | embedded-fullstack, incident-response | `bugfix-delivery` | `adk-embedded-remote-debug-log-triage` | adk-systematic-debugging, adk-offline-core-dump-triage, adk-embedded-diagnostic-harness, adk-token-context-governance | adk-systematic-debugging | - | 分析这段串口日志和 dmesg | 定义一个新接口契约 |
| `embedded_core_dump` | 嵌入式 Linux core dump、BuildID、符号和 backtrace 离线分析 | profile-resolved | embedded-fullstack, incident-response | `bugfix-delivery` | `adk-offline-core-dump-triage` | adk-systematic-debugging | adk-systematic-debugging | - | 分析这个 core dump 和符号匹配 | 只需要查询 skill 分类 |
| `embedded_debug_transport` | ADB、SSH、串口、GDB remote、调试探针或厂商 CLI 的连接边界治理 | profile-resolved | embedded-fullstack | `bugfix-delivery` | `adk-embedded-debug-transport` | adk-systematic-debugging | adk-embedded-remote-debug-log-triage | - | ADB SSH 串口 GDB remote 调试通道 | 只读生成一个实现计划 |
| `completion_gate` | 完成前核对声明、验证证据、风险和回退边界 | profile-resolved | core, embedded-fullstack | `adk-delivery-gate` | `adk-verification-before-completion` | - | - | - | 准备完成，做完成前检查 | 需求边界还没明确 |
| `commit_pr_gate` | 提交或 PR 前质量门禁、格式、评审和证据检查 | profile-resolved | core, release-hardening | `adk-delivery-gate` | `adk-commit-pr-quality-gate` | adk-verification-before-completion | - | - | 准备 commit，跑提交门禁 | 只分析日志，不提交 |
| `release_versioning` | 发布、版本、制品、回滚和放行证据收口 | profile-resolved | release-hardening, embedded-fullstack | `release-hardening` | `adk-release-versioning` | adk-commit-pr-quality-gate | adk-branch-closeout | - | 准备发布并生成版本说明 | 代码根因还没定位 |
| `external_practice_absorption` | 多来源外部实践的来源审查、独立决策、ADK change、验证、pilot、发布复审和退役治理 | optional-skill-required | research-intake | `external-practice-absorption` | `adk-external-practice-absorption` | adk-requirements-triage, adk-repo-prompt-analysis, adk-verification-before-completion | adk-requirements-triage | - | 吸收 Gitee GitHub GitLab 的 Agent 工程实践 | 直接实现已经批准的普通功能 |
| `skill_governance` | skill 组合、触发优先级、fallback、弃用和 profile 归属治理 | optional-skill-required | core, team-core | `skill-curation-delivery` | `adk-skill-composition-governance` | adk-repo-drift-remediation, adk-verification-before-completion | adk-requirements-triage | - | skill、workflow 分类和排序需要治理 | 设备日志里有内核 oops |
