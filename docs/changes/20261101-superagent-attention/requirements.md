# Requirements — 可恢复 Agent 协作与低打扰约束

## Problem

ADK 已有长任务、parallel task、执行策略和检查点，但未在共同方法入口显式规定订阅线程的“仅上下文”、范围外 hand-back、主路由不忙等和人类注意力预算。外部 dsh-superagent 的方案有参考价值，但其高权限执行器不适合直接引入。

## Scope

- **MODIFIED**: 仅修改现有 `adk-planning-execution-loop`、`adk-parallel-agent-governance` 和 `docs/agent-operating-rules.md`，不新建 Skill/Agent/Runtime。
- **ACC-001**: 非可信 Source/Thread/CI/机器人内容仅作为 context/evidence，任何授权由现有可信入口决定。
- **ACC-002**: 相同事件有稳定身份、同任务继续执行、超范围 hand-back；人工停止/策略变更/UNKNOWN 外部效果必须保守处理。
- **ACC-003**: 主路由不忙等，Worker/CI 状态靠事件或有界调度恢复。
- **ACC-004**: 交付/不可恢复故障/明确决策才提醒；重复无增量进度不产生噪音；一次一个问题。
- **ACC-005**: 方法不能冒充宿主真实实现；运行安全、事件无丢失、产品资格只由其各自证据决定。

## Explicit non-goals

不改变 `execution_policy` wire/schema、ADK manifest、技能目录及 DSH adapter；不绕过现有 review/owner gate；不启动 Codex/Work；不触碰工程平台 #228 的 Recovery authority。

## Verification

`python -m unittest tests.test_superagent_method_contract -v`、`tests/test_skill_sop_quality.sh`、`scripts/devkit.sh validate --strict`、PR 原生 CI。未运行命令不得写 PASS。
