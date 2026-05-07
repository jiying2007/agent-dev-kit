# Runbooks

按场景提供可直接执行的 Agent/Skill 组合与命令序列，默认遵循 `propose -> apply -> verify -> archive`。

## 场景列表

- `feature-delivery.md`：需求到交付
- `bugfix-delivery.md`：缺陷修复从定位到闭环
- `refactor-hardening.md`：重构场景的风险压实与回归门禁
- `codex-runtime-pilot.md`：在 `~/.codex` 的真实运行闭环验证
- `adk-cross-team-handoff-delivery.md`：跨团队交接与签收闭环
- `large-platform-delivery.md`：大型工程的模块边界与关键触点治理
- `evidence-index-delivery.md`：证据索引化交付与审计回放
- `migration-stage-delivery.md`：阶段式迁移交付与里程碑验收
- `config-baseline-governance.md`：配置基线治理与漂移审计
- `codex-settings-audit.md`：codex 运行配置审计与加载一致性校验
- `spec-chain-delivery.md`：requirements/design/tasks 规范链路交付
- `skill-curation-delivery.md`：技能候选筛选与归属决策交付
- `prompt-evolution-delivery.md`：提示词演进与回归对比交付
- `lead-agent-convergence-delivery.md`：多轮协作收敛与轻量工件闭环
- `driver-bringup.md`：新外设驱动上板联调
- `release-hardening.md`：发布前收口与风险压实
- `artifact-gated-delivery.md`：高风险变更的轻量产物门禁
- `openspec-bridge.md`：openspec 与 adk 变更工件桥接
- `runtime-routing.md`：`~/.codex` 运行入口与技能路由仲裁
- `adk-planning-execution-loop.md`：长任务计划审查、执行检查点与跨会话恢复
- `production-deployment.md`：生产安装、备份、健康检查与回滚
- `upstream-intake.md`：参考仓同步、候选评估与回灌闭环
- `compatibility-matrix.md`：多工具转换能力与降级边界
- `adk-security-supply-chain.md`：第三方资产引入前安全与供应链审查
- `team-delivery.md`：团队责任矩阵、交接签收与复验闭环

## 使用方式

1. 先执行 `bash scripts/devkit.sh catalog build`，确认当前可用能力。
2. 按场景文档选择 Agent 流程与 Skill 组合。
3. 执行对应命令模板，并在 `docs/changes/<change-id>/` 留存工件。
