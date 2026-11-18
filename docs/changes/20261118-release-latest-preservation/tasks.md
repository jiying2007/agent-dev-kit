# 历史发行补发保留 latest：执行与验证

| 阶段 | 内容 | 验收依据 |
|---|---|---|
| 1 | 明确 current/backfill 身份与 latest 参数，保持原发布门禁 | 本候选实际 diff；独立 Spec/Quality review |
| 2 | 执行真实 workflow 片段的状态回归和身份负例 | 原 release-manifest 组及完整回归的实际 CI 结果 |
| 3 | 受保护合并并发布不可变 11.4.4，核验 latest | 本候选 PR、main CI、发行工作流、Release 与 latest API |
| 4 | Root 使用原 helper 消费 exact source 并验证主线 | 原生成回执、仅两路径消费 diff、Root PR/main CI |

编辑环境为源文件快照，无真实 `rtk`，未在此环境执行项目测试。验证使用现有 GitHub Actions；启动、静态审查或命令存在不代表已通过。完整 checkout 的恢复入口为 `rtk tests/test_release_manifest_contract.sh`、`rtk tests/run_all.sh` 和 `rtk scripts/devkit.sh release check`。

执行状态与结果保留于关联 PR 的独立审查、Actions 和发行原件；本表定义验收，不另建结果台账。实际失败在本 change 的 `negative-results.md` 保留。无付费模型、宿主或现场运行，相关效果仍为未测。
