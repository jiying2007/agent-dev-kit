# 设计说明：remove-external-runtime-compat

## 架构影响
- `adk-runtime-router` 只在 ADK inventory 内选择 primary/supporting；外部参考仓不再是 runtime fallback provider。
- 删除 fallback sunset 专用控制面；pilot readiness 继续独立验证 evidence file、状态和 readiness 维度。
- 根工作区 reference lifecycle 与 ADK production manifest 保持单向关系：reference 可供 intake，不能成为运行依赖。

## 数据与配置影响
- 删除 `docs/reference/fallback-sunset-matrix.{md,tsv}`、`scripts/check-fallback-sunset.sh` 和对应测试入口。
- 更新当前 pilot、workflow 文档和 runner，去掉 fallback matrix 生成证据。
- 更新 routing fixture，使显式旧名称只作为意图词，预期结果仍是 ADK Skill。

## 兼容性与迁移方案
- Breaking change：不再提供外部流程兼容 Skill/profile。
- 迁移：brainstorm/review/debug/plan/worktree/closeout 等请求按 ADK route table 映射。
- 团队 Codex 资产只接受 clean、checksum 绑定的 ADK bundle；live apply 前必须审查 prune plan。
- 回滚：恢复上一 clean ADK bundle，并走同一 plan/dry-run/apply 链。

## 验证策略
- `rtk bash tests/test_skill_trigger_matrix.sh`
- `rtk bash tests/test_match_effectiveness.sh`
- `rtk bash scripts/pilot-readiness.sh --summary-json`
- `rtk bash scripts/devkit.sh validate --strict`
- `rtk bash tests/run_all.sh --fail-fast`
- 根仓轻量/ADK harden 门禁；clean release 后再执行团队 bundle import 与完整 source-to-live。
