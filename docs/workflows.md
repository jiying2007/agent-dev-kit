# Workflow 与普通 Skill 的使用边界

**Workflow 是声明式交付契约，不是模型执行器或常驻调度器。** 只有 `manifest.json:workflows` 登记的资产及对应 `workflows/<name>/WORKFLOW.md` 才是正式 Workflow。其他“场景 A/B/C”、Runbook、Skill 组合只是任务建议，不得扩张成第二套路由、权限或工作流列表。

## 实际登记的 Workflow

| Workflow | 何时使用 | 权威契约 |
| --- | --- | --- |
| `feature-delivery` | 新功能、多模块行为变更 | [feature-delivery](../workflows/feature-delivery/WORKFLOW.md) |
| `bugfix-delivery` | 需要复现、修复和回归的缺陷 | [bugfix-delivery](../workflows/bugfix-delivery/WORKFLOW.md) |
| `release-hardening` | 发布前的质量、安全、版本与回滚收口 | [release-hardening](../workflows/release-hardening/WORKFLOW.md) |
| `runtime-routing` | 能力选择、主技能、fallback 与 profile 校验 | [runtime-routing](../workflows/runtime-routing/WORKFLOW.md) |
| `skill-curation-delivery` | Skill 候选审核与 core/optional 归属 | [skill-curation-delivery](../workflows/skill-curation-delivery/WORKFLOW.md) |
| `external-practice-absorption` | 经过审核的外部方法吸收，需明确可选能力范围 | [external-practice-absorption](../workflows/external-practice-absorption/WORKFLOW.md) |
| `adk-delivery-gate` | ADK 资产本仓的验证/Review/归档门禁 | [adk-delivery-gate](../workflows/adk-delivery-gate/WORKFLOW.md) |

实际可用性依赖 Profile 与可选 Skill 安装范围。表格是人类入口，具体主/辅关系、命令风险及执行边界以 `manifest.json` 和对应 Workflow 契约为准，不维护独立镜像。

## 普通开发任务：不等于新增 Workflow

| 任务 | 建议先看 | 交付重点 |
| --- | --- | --- |
| 已明确的小修 | [按任务使用](usage.md) | 直接改最小范围，跑定向测试，不强制建完整 Change Contract |
| 头脑风暴 / 方案拷问 | `adk-structured-requirements-questioning` | 多轮探索关键决策与反例；明确计划则不重复访谈 |
| 规格驱动、跨 SoC/MCU 协议 | [SDD 最小路径](runbooks/spec-driven-delivery.md) | 唯一规格身份、双方契约测试、真实集成结论 |
| 嵌入式 Bring-up 或故障 | [驱动 Bring-up](runbooks/driver-bringup.md) | 时钟/复位/IRQ/驱动证据与 HIL/SIL 缺口 |
| 长任务与 Goal 恢复 | [计划执行](runbooks/planning-execution-loop.md) | 复用已验证成果、可恢复下一动作，不循环写计划 |
| 跨团队交接 | [交接 Runbook](runbooks/cross-team-handoff-delivery.md) | Owner/接口/交接验收，不能借工作流授予权限 |
| 代码审查与分支收口 | [代码/分支 Skill 目录](agent-skill-catalog.md) | 真实 diff、风险分级、最终测试与可撤销动作 |
| 事故总结与研究归档 | [可选能力说明](usage.md) | 权限与范围先确认，不自动把附件升级为生产证据 |

Skill 的准确触发和排他规则属于 `manifest.json:routing`，而不是本表。需要真实目标可用性时，单独做 native discovery/load/trigger 及权限验证，不能因为文档列出名称就声称已安装。

## ADK Change 工作流的五个动作

`propose → apply → verify → review → archive` 是**本仓受治理 Change** 的操作语义，不是每个用户请求的强制流程。`verify` 失败应保持失败事实，修复后复测；`review` 不能替代独立核验；`archive` 不等价发布或产品认证。精确状态转换与产物字段请读取[正式 Workflow 契约](../workflows/adk-delivery-gate/WORKFLOW.md)，不要从该摘要反向生成第二套合同。

Workflow 源码维护可使用：

```bash
bash scripts/devkit.sh validate --strict
bash scripts/check-workflow-closure.sh --profile core
bash tests/test_workflow_contract.sh
```

发布前仍以最终 HEAD 的[完整回归与 Release 门禁](runbooks/workspace-maintenance-guide.md)为准。Workflow IR 只用于编译、验证与分发，不能执行模型、生产工具、调度或外部写入。
