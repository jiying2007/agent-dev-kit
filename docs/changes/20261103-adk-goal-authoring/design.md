# 设计

ADK新增adk-goal-authoring及typed goal_plan模块，统一adk.goal-plan/v1合同。CLI公开goal plan-check/render/resume；goal check继续检查ADK产品目标，state-check继续状态卫生检查，既有命令无语义变化。

Goal生成与需求澄清、任务拆解、长期执行分界：本技能生成可验证目标合同和当前批次；执行交给既有planning-execution-loop。检查不证明业务证据、不操作原生Goal，也不建立第三套预算引擎。

gros_compile将现有合同schema切换为ADK并更新入口命令，README指向恢复流程。现有完整目标与历史保持。Codex已安装local技能在正式exact导入前保持原身份，不能伪造ADK来源；不删除既有运行能力。

回退：撤回本次新增ADK资产与CLI分支、项目schema/入口的精确差异；不回退用户业务或旧脏改。正式导入依赖缺失时单列NEEDS_REVIEW，完成本地可验证部分。

新增core技能的来源增长核对（author-self-review）：入口4457字节、延迟示例1864字节。仅对core及其继承profile的既有source-growth ratchet各增加上述精确增量和一个asset；其他profile不变。它是经本次用户新增能力请求解释的源码增长，不是运行时token预算放宽，Codex常驻数未增加。原基线身份保留在note，增长负例必须仍能失败。
