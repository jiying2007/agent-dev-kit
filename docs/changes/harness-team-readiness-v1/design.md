# 设计说明：harness-team-readiness-v1

## 架构影响

- 新增 `src/agent_dev_kit/readiness.py`，只负责加载合同、有限扫描目标仓、评估七个维度和渲染 Markdown。
- `src/agent_dev_kit/cli.py` 增加 `harness readiness` 命令；默认 report-only，`--gate` 才把非 `pass` 总状态映射为退出码 2。
- 新增 `manifests/harness_readiness_contracts.json` 作为维度、状态、扫描预算、敏感字段和证据路径的单一事实源。
- 在 `adk_capability_health_contracts.json` 增加一条现有 goal/agent/skill/workflow 到新命令、测试和文档的闭环，不新增平行 workflow 或 Skill。

## 数据与配置影响

报告顶层字段：

- `schema_version`、`contract_version`、`mode`、`target_root`、`overall_status`、`counts`、`scan`、`dimensions`。

每个 dimension 固定字段：

- `dimension_id`、`title`、`status`、`evidence_refs`、`last_verified_at`、`owner`、`blockers`、`next_action`。

目标仓可选提供 `.adk/harness-readiness.json`，声明七个维度的 `owner` 与 `last_verified_at`；缺失元数据不会伪造负责人或验证时间，自动检测本可为 `pass` 的维度会降为 `partial`。验证时间受 90 天 freshness 和未来日期门禁约束。工具系统不存在时允许 `not-applicable`；MCP 存在时还必须在工具维度声明结构化 `permission_boundary`，硬编码敏感值必须 `blocked`。

## 判定规则

七个维度不加权、不汇总成分数：

1. `context_legibility`：根 `AGENTS.md` 与 `README` 可发现，AI 入口不过度膨胀。
2. `spec_and_execution_contract`：存在 spec/design、task/plan 和验收/验证工件。
3. `tool_and_permission_boundary`：MCP 配置可解析、依赖固定、凭证引用环境变量且有权限边界；没有 MCP 配置时为 `not-applicable`。
4. `state_and_knowledge_continuity`：有变更状态以及 decision/runbook/knowledge 等长期记录。
5. `verification_review_and_eval`：测试、CI 和可执行验证说明形成闭环。
6. `recovery_and_rollback`：存在可发现的 rollback/recovery/backup 说明或入口。
7. `freshness_and_entropy_control`：存在文档/格式/目录新鲜度检查和 ownership 证据。

总状态优先级为 `blocked > needs-review > partial > pass`；`not-applicable` 不降低总状态。任一扫描预算被截断时，受影响报告不得给出完全就绪结论。

## 安全与性能边界

- 通过排序后的 `os.walk` 扫描，排除合同声明的依赖、缓存、构建和 VCS 目录。
- 不跟随符号链接，不执行目标仓文件，不访问网络。
- 仅解析候选 MCP JSON；敏感 key 命中时保留 `relative/path.json#json.key.path`，不保留 value。
- 报告输出使用原子替换，CLI 异常沿用 ADK 统一错误边界。
- Python 代码遵守当前 3.11+ 发布基线，不增加 Harness 专属第三方依赖。

## 兼容性与迁移方案

- `scripts/quality-gates.sh <change-dir>` 保留命令路径并改为带弃用提示的包装层，但检查语义切换到 canonical change contract；这是显式行为 breaking change。
- `changes/README.md` 只保留迁移说明，canonical 工件仍为 `docs/changes/`。
- 迁移顺序：先用 `devkit.sh propose` 建立 `docs/changes/<id>/`，迁移 proposal/design/tasks/checklist/negative-results，再调用 canonical checker；旧工件在迁移确认前不得删除。
- 现有 `harness-loop-engineering` 命令保持不变：它验证 ADK 自身 Harness/loop 合同；新命令检查目标仓证据，两者边界互补。
- 回滚只需撤销本 change 触及的 CLI、Python、manifest、fixture、测试和文档；没有数据迁移或运行时安装。

## 验证策略

- 合同检查：`rtk agent-dev-kit/scripts/devkit.sh harness readiness --root agent-dev-kit/fixtures/harness-readiness/pass/team-repo --summary-json`
- 负向脱敏：对 hardcoded-secret fixture 必须输出 `blocked` 与 key path，且报告不得包含 secret value。
- Gate 行为：正向 fixture `--gate` 返回 0；负向和证据不足 fixture返回 2。
- 定向回归：`rtk agent-dev-kit/tests/test_harness_readiness.sh`、`rtk agent-dev-kit/tests/test_capability_health.sh`、`rtk agent-dev-kit/tests/test_docs_cli_alignment.sh`。
- ADK 门禁：`rtk agent-dev-kit/scripts/devkit.sh validate --strict`、`rtk agent-dev-kit/tests/run_all.sh --quick`、`rtk agent-dev-kit/tests/run_all.sh`。
- 仓库级门禁：`rtk scripts/check-all.sh --quick` 与 `rtk bash ~/codex/scripts/final-ready.sh`；无法执行项写明原因和风险。
