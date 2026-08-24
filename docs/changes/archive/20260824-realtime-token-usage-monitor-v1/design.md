# 设计说明：realtime-token-usage-monitor-v1

## 架构影响
- D1：新增 `src/agent_dev_kit/token_monitor.py`，只负责事件校验、归一累计、状态机、速率/ETA
  和可序列化 state；不读取 runtime 私有数据源。
- D2：`cli.py` 新增 `token monitor`，从 stdin 或显式文件逐行读取并立即 flush JSONL；provider
  adapter 是上游责任。
- D3：采用 event-sourcing 风格：`event_id` 幂等，delta 追加，snapshot 按 scope 单调推进；
  这吸收 Temporal replay 和 LangGraph checkpoint 的通用思想，但不引入其依赖。
- D4：状态等级只由确定性阈值计算，动作只是建议。长任务执行器可消费 `checkpoint/compact/stop`，
  本变更不自动执行副作用。

## 数据与配置影响
- D5：事件 schema `token_usage_event/v1`；逐事件输出 `token_monitor.event/v1`；最终输出
  `token_monitor.summary/v1`；state 使用 `token_monitor.state/v1`。
- D6：累计总量只使用 `total_tokens`；其他 Token 字段独立累计用于构成分析，避免 OpenAI
  cached-as-subset 与 Anthropic cache-separate 语义被 core 错误混算。
- D7：状态文件使用同目录临时文件 + `os.replace` 原子更新；恢复时校验 budget/threshold contract。
- D8：不新增 manifest asset；这是 typed core CLI 能力。目标契约和测试入口通过现有 package/export
  与 regression runner 分发。

## 兼容性与迁移方案
- 新命令为 additive change；现有命令无参数或输出变化。
- adapter 最小迁移是把 provider usage 映射为 canonical `total_tokens` 和稳定 `event_id`。
- 对不能判断 cache 语义的数据源，adapter 必须从 provider 自带总量取值或拒绝，不在 core 推断。
- 回滚只删除新命令/module/test/docs；无运行态数据库迁移。

## 验证策略
- 单元/CLI：`rtk agent-dev-kit/tests/test_token_monitor.sh`。
- 性能/流式：测试内生成 1000 条 canonical events，验证输出行数、最终累计和无正文泄漏。
- 结构：`rtk agent-dev-kit/scripts/devkit.sh validate --strict`。
- 回归：`rtk agent-dev-kit/tests/run_all.sh --quick`，再按共享 CLI 风险升级 full。
- 根仓：`rtk scripts/check-adk-harden-readiness.sh .` 与 `rtk scripts/check-all.sh --quick`。

## 外部一手证据与可迁移边界

- OpenAI Agents SDK usage：逐 run usage 可访问，checkpoint 会保留累计 usage；采用“usage 可被执行器
  消费、恢复时保留累计”的合同，不引入 SDK。
  `https://openai.github.io/openai-agents-python/usage/`
- OpenAI Agents SDK tracing：trace/span 可按 workflow/group 关联，敏感数据可关闭；采用 `scope_id`
  与不保存正文的边界。
  `https://openai.github.io/openai-agents-python/tracing/`
- LangGraph interrupts：checkpoint + thread cursor 恢复，恢复会重跑 node，副作用应幂等；采用 event_id
  去重和 monitor 无副作用原则。
  `https://docs.langchain.com/oss/python/langgraph/interrupts`
- Temporal Python SDK：workflow history replay 要求确定性；采用 snapshot 单调校验和可重放 state，
  不采用其 runtime/worker 模型。
  `https://github.com/temporalio/sdk-python`
- Anthropic context editing：旧 tool result 清理由 Token 阈值触发，且清理会影响 prompt cache；采用
  `compact` 作为建议而不是自动动作，阈值由 owner 配置。
  `https://platform.claude.com/docs/en/build-with-claude/context-editing`

## Tool / Skill Evidence Plan

- primary_skill：`adk-planning-execution-loop`。
- supporting_skills：`adk-token-context-governance`、完成前使用
  `adk-verification-before-completion`。
- required_artifacts：requirements/design/tasks/state/session-state/negative-results、源码、测试、
  before-after、review、verification evidence。
- skipped：Superpowers（ADK 已覆盖）；并行 agent（共享 CLI/contract，不满足独立边界）。
- tool_fallback：外部网页不可用时回退仓内 official freshness manifest 与本地参考仓原文。
