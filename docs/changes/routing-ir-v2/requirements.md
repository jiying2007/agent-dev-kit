# 需求：routing-ir-v2

## 目标

- 将运行时短语路由、任务模式、否定语义、变更权限和弃权结果收敛到 `manifest.json:routing` 的单一结构化合同。
- 保持现有正向路由的 primary Skill 兼容。
- 对组合否定和只读边界返回确定性的 `abstain / needs_triage`，不得继续落入 Skill trigger fallback。

## 范围

- 修改 `manifest.json`、兼容镜像 `manifest.yaml`、`manifests/manifest.schema.json` 和 `src/agent_dev_kit/matcher.py`。
- 更新路由确定性测试与本 change 的复现、设计和验证证据。
- 不修改 Skill 正文，不改变 Profile 组成，不启用 runtime、MCP、Hook 或外部写入。

## 验收标准

1. `routing.ir_version` 固定为 `routing-ir/v2`。
2. 合同显式声明 task mode、mutation permission、per-intent negated intents 和 abstain policy。
   task mode 与 mutation permission 必须使用 canonical 安全配对；routing task mode 必须显式映射到
   Runtime Control v2 的 `readonly|implementation|release` artifact mode，`needs-triage` 不得进入 gate。
3. 以下输入不得命中原 Skill，必须非零退出并返回 `decision=abstain reason=needs-triage task_mode=readonly mutation_permission=deny`：
   - `长任务但只做只读分析且无需执行计划`
   - `根因不明但不要调试只做架构评估`
   - `准备发布但只需要解释现状不执行发布`
4. 对应正向输入仍分别命中 `adk-planning-execution-loop`、`adk-systematic-debugging`、`adk-release-versioning`。
5. 原有路由测试、schema 校验和 ADK quick regression 通过。
6. intent 自身权限是不可放宽的上限；请求中的 `修复/实现` 信号不得把 debugging/review 提升为 workspace-write。
7. 被明确否定的 non-trigger 不得 veto 后续正向 intent。

## 风险与回滚

- 风险：过宽否定词可能压制合法的“只规划、不发布”请求。
- 控制：组合否定使用 `all_of`，局部否定只压制被否定的具体触发短语；不以单个通用“不”否定整条意图。
- 回滚锚点：移除 routing v2 字段和 matcher 的否定/弃权分支即可恢复原始正向短语匹配路径。
