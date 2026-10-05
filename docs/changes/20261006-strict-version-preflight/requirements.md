# Strict 版本身份预检

目标：`validate --strict` 非 quick 路径提前拒绝版本投影缺失或漂移，复用 `versioning.version_identity_failures`，避免仅在 `release check` 才暴露身份错误。

边界：仅修改 `validation_contract.py`、`tests/test_validate.sh` 与本 change 的 requirements/design/tasks。保持 `--quick`、`--strict --quick` 的原有范围；不修改版本、manifest、lock、CI 或发布逻辑，不运行真实模型，不 commit/push，不更新 live。

验收：当前源码 strict/quick 基线通过；真实 CLI 消费者针对 `CONTEXT.md` 与 `manifests/software_m5_eval_contract.json` 任一投影的缺失及版本漂移返回 fail；quick 与 strict+quick 继续通过；新鲜定向验证和差异检查可复跑。

风险：strict 非 quick 会新增版本身份失败，旧的漂移源码将被提前阻断；诊断完全复用 release 的现有身份检查。主线程负责整体回归、独立 review 和交付收口。

追加 scope：主线程在下一轮候选 full suite 发现唯一 `test_file_modes` 失败后，授权只修正 `scripts/check-file-modes.sh`、`tests/test_file_modes.sh` 与本 change 三份文档。支持合法 `.git` 文件的 Git worktree，Git 返回的真实 toplevel 必须等于 requested physical root；拒绝非仓库、借用父仓和坏 gitfile。显式 inventory、`--fix` 和 mode-only 的 deleted-file 语义保持不变，不修改前轮 strict validator/test_validate、版本、manifest、CI 或 main 交付源。
