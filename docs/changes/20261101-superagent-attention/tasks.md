# Tasks

| ID | State | Task | Evidence |
| --- | --- | --- | --- |
| TASK-001 | IMPLEMENTED — verify pending | 在现有 planning execution Skill 写入事件幂等/权限/恢复/低打扰契约 | `skills/adk-planning-execution-loop/SKILL.md` |
| TASK-002 | IMPLEMENTED — verify pending | 在并行治理 Skill 写入 Router/Worker hand-back 和任务身份合同 | `skills/adk-parallel-agent-governance/SKILL.md` |
| TASK-003 | IMPLEMENTED — verify pending | 在通用 Agent 规则同步边界而不冒充宿主授权 | `docs/agent-operating-rules.md` |
| TASK-004 | IMPLEMENTED — verify pending | 增加 positive/negative typed intake 和方法资产回归 | `tests/test_superagent_method_contract.py` |
| VERIFY-001 | NOT RUN locally | Python 定向 unittest | `python -m unittest tests.test_superagent_method_contract -v` |
| VERIFY-002 | NOT RUN locally | ADK strict、Skill SOP、GitHub PR CI | 以 Actions exact head 回执为准 |
| REVIEW-001 | PENDING | 独立评审 diff/行为界限 | 实际 GitHub reviewer/验证，不伪造 |
| ARCHIVE-001 | PENDING | 归档版本/证据与后续平台差异 | PR 合入及 fresh-main |

原始 Root 评估入口：`jiying2007/llm_agent#285`。此 change 仅覆盖 ADK 方法层；工程平台事件投递/通知运行层需单独验收。
