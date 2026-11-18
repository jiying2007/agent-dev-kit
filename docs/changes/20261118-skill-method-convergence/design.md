# Skill 方法沉淀：设计

## 七字段方法记录

| 字段 | 本次记录 |
|---|---|
| 问题与证据 | 11.4.2 源码中来源治理使用不同决策措辞、E2/E3 同时用于执行投入与证据、文档强制重复记录；现有评测、触发和导出机制已存在，继续增设体系会产生第二事实源。对照父提交 `0a6bf985de5e2d3523cd4e82cb19d3b8575a4fdb` 的目标文件。 |
| 方法机制 | 在原治理与 authoring 入口消歧并补最小可追溯记录；使用现有任务和合同检查验证可消费性，质量改善须另由真实测量证明。 |
| 适用与不适用条件 | 适用于 Skill 来源吸收、编写、评测和迭代。普通任务使用按需加载；本变更不启用当前不可达的 E1 路由，不授予执行或发布权限。 |
| 资产归属 | ADK 负责平台中立资产、格式与评测规则；Root 负责来源决策、问题导航和消费。原 owner 与 manifest 保持；不新增 Skill 身份。 |
| 来源与取舍 | 基于两仓当前原件与现有测试。Root 契约基线 `761e41b28b93b6b3fb5b8c451870afb0c45e0c5a`。不引入新的外部方法或代码；保留历史来源，避免浮动 URL 被误当固定证据。 |
| 验证与效果 | 复用下表的确定性检查、受保护 CI 及实际独立审查。模型质量、Token、费用、真实延迟和宿主效果为 `not-measured`；开发任务解答只检验 verifier，不是模型 trial。 |
| 维护与退出 | 新失败、触发冲突、合同/平台变化或重复机制出现时复核。使用原 owner、变更合同与 review trigger；回滚为新的受保护修复提交/版本，已发布标签不可移动。 |

## 分批覆盖与验证入口

| 批次 | 实际覆盖 | 原有验证入口 |
|---|---|---|
| 规范收敛 | 格式、来源决策、评测、生命周期、执行规则与消费导航 | `tests/test_skill_quality_methods.py`、`tests/test_skill_method_efficiency.py`、strict validation |
| 三类重点能力 | `adk-planning-execution-loop` → `goal-resume`；`adk-structured-requirements-questioning` → `intent-distinction`；`adk-code-review-loop` → `review-false-positive` | `tests/fixtures/skill_execution_tasks/suite.json`、`tests/test_skill_execution_tasks.py`；均为 development/test-only |
| 全量维护 | 56 core + 9 optional；名称/触发边界、负例、引用自包含、组合与导出 | `tests/test_skill_trigger_matrix.py` 由独立 `tests/test_skill_trigger_matrix.sh` 运行；`tests/test_skill_content_contract.py`、`tests/test_skill_portfolio_quality.py`、`tests/test_skill_consumer_usability.py` 由 `tests/test_skill_content.sh` 运行；两组均纳入原 `tests/run_all.sh` |
| 发布消费 | 本候选自己的 PR/main CI、11.4.3 不可变发行、Root exact-source 消费 | 原 release-tag-promotion 与 Root consumer CI；无发行则不推进 gitlink |

不新增仅镜像文档实现的测试，不因三类示例已暴露而重命名为 holdout。真实效果试验需未来已有授权的运行渠道、预注册条件和原始 Trace；本变更不预填结果。
