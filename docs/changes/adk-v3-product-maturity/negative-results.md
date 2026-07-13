# Negative Results: adk-v3-product-maturity

| Command | Exit | Before-fix result | Resolution |
|---|---:|---|---|
| `rtk bash tests/test_product_maturity_v3.sh` | 1 | `[FAIL] v3 manifest schema missing` | 增加 JSON schema、类型化 core 和 3.0 CLI |
| `rtk bash tests/test_product_maturity_v3.sh` | 1 | `[FAIL] release workflow still treats Codex as a direct target` | Release 只构建三个 direct targets，Codex 改为 external handoff metadata |
| `rtk bash tests/test_product_maturity_contracts.sh`（root） | 1 | `[FAIL] product maturity model missing` | 增加成熟度模型、scorecard、task pack 和 report registry |
| `rtk bash scripts/convert-assets.sh --target codex --profile embedded-fullstack --out /tmp/adk-release-negative --dry-run` | 1 | `[FAIL] unsupported target: codex` | 删除 release workflow 中无效调用，release check 阻断回归 |
| `rtk python3 -m pip wheel --no-deps --no-build-isolation .` | 0 but invalid | 旧 setuptools 45.2 生成 `UNKNOWN-0.0.0` | 正式 wheel 使用 build isolation，产出 `agent_dev_kit-3.0.0`；无效残留已清理 |
| 初始 Codex 30-task A/B | diagnostic | baseline `23/30`、ADK `27/30`，共享 safety policy 不充分 | 保留原始结果；统一显式审批策略后最终为 `27/30` 与 `30/30`，不覆盖失败证据 |
| 隔离 wheel 后 `adk validate --quick`（显式 `--no-deps` 安装） | 1 | `PyYAML is required while manifest.yaml compatibility exists` | 安装声明依赖 `PyYAML>=5.3,<7` 后通过；证明缺依赖时明确失败而非静默跳过兼容检查 |
| `rtk claude auth status` | 1 | `loggedIn=false` | runtime eval 明确记录 `not-run`，不虚构 Claude 结果 |
| `rtk bash tests/run_all.sh --full ...` | 1 | runner 不支持冗余 `--full` 参数 | 使用无 `--quick` 的默认完整模式并刷新 timing JSON；验证报告命令已修正 |

所有失败均保留为 before-fix 或外部前置条件证据；未通过的 Claude runtime 不计入完成声明。
