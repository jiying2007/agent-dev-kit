# Tasks

| ID | State | Task | Evidence |
| --- | --- | --- | --- |
| TASK-001 | IMPLEMENTED — verify pending | 在现有 planning execution Skill 写入事件幂等/权限/恢复/低打扰契约 | `skills/adk-planning-execution-loop/SKILL.md` |
| TASK-002 | IMPLEMENTED — verify pending | 在并行治理 Skill 写入 Router/Worker hand-back 和任务身份合同 | `skills/adk-parallel-agent-governance/SKILL.md` |
| TASK-003 | IMPLEMENTED — verify pending | 在通用 Agent 规则同步边界而不冒充宿主授权 | `docs/agent-operating-rules.md` |
| TASK-004 | REPAIRED / CI PENDING | 新测试纳入现有 full/quick 治理回归入口；prototype 有合法证据正例，逐项断言权限与退出门禁错误 | `tests/test_superagent_method_contract.py`、`tests/test_intent_boundary_governance.sh` |
| VERIFY-001 | NOT RUN locally | Python 定向 unittest | `python -m unittest tests.test_superagent_method_contract -v` |
| VERIFY-002 | NOT RUN locally | ADK strict、Skill SOP、GitHub PR CI | 以 Actions exact head 回执为准 |
| REVIEW-001 | FIRST REVIEW HOLD / RE-REVIEW REQUIRED | 独立 AI Review #5726254267 发现 M01/M02 和 N01/N02；已根据意见实施修复，新的 exact HEAD 必须重审后方可签新的 Harness 记录 | [Review #5726254267](https://github.com/jiying2007/agent-dev-kit/pull/229#pullrequestreview-5726254267) |
| ARCHIVE-001 | PENDING | 归档版本/证据与后续平台差异 | PR 合入及 fresh-main |

原始 Root 评估入口：`jiying2007/llm_agent#285`。此 change 仅覆盖 ADK 方法层；工程平台事件投递/通知运行层需单独验收。
