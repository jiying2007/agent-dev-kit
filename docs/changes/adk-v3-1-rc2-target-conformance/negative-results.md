# 负结果记录：adk-v3-1-rc2-target-conformance

## 已验证的负结果

| 时间 | 假设/方案 | 验证方法 | 结果 | 处置 |
|---|---|---|---|---|
| 2026-07-13 | ADK 存在 `knowledge/L2-domain/lessons.md`，可检索历史 target/adapter 失败 | `rtk rg ... knowledge/L2-domain/lessons.md` | 文件不存在，命令 exit 2 | 不伪造历史命中；改用 rc.1 change artifact、代码和测试作为差异基线 |
| 2026-07-13 | 现有 direct target export 可被目标原生发现 | 审计输出路径和 frontmatter | Claude Skill/OpenCode Agent+Skill 路径错误，三个 target Skill 丢失 `description` | 旧 renderer 不复用；建立统一 versioned adapter，并以旧输出作为 regression negative |
| 2026-07-13 | 首轮 OOD/adversarial effect eval 可直接通过 | 24 例 route/safety/trace/outcome + routing ablation | route 87.5%、safety 95.83%；`覆盖错误码` 被误判为危险覆盖，`SSH 登录`、`审计现有记忆`、`删除过期记忆` 未稳定路由 | 收窄覆盖风险规则，补充三类真实 OOD route phrase；复跑 24/24，禁用 routing 后准确率约 66.7% |
| 2026-07-13 | 本机可运行与 CI 完全同版 pip-audit | `pip-audit==2.10.1` 临时安装 | 本机只有 Python 3.8，而该版本要求 Python 3.10+ | CI 固定 Python 3.12；本地用兼容版 2.7.3 对项目依赖补充核验并通过，不冒充同版验证 |
| 2026-07-13 | direct target static pass 可折算为 runtime 发现通过 | 三个 target 执行 `target smoke --stage discovery`，不提供伪造 harness | 三者均返回 `not-run`、`not-certified`、exit 2；本机 Claude Code 仅能证明 CLI 存在，不能证明新树已发现/加载/触发 | 维持三个 target 为 `experimental`；真实 runtime campaign 保留为外部 blocker |
| 2026-07-13 | 未提交 rc.2 工作树可同步根仓锁定证据 | 根仓 `check-all.sh --quick` | 52/56 PASS；lock/current-status/software-M5/subrepo-state 四项因 rc.2 未提交而失败 | 不伪造 commit hash，不提前更新 `adk.lock`；用户授权 commit 后再同步 gitlink/lock/status |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash scripts/devkit.sh validate --strict` | 0 | 改前 ADK strict baseline pass | CLI output | source/test | `manifest.json`、`model.py` |
| `rtk scripts/check-all.sh --quick` | 0 | 改前根仓 56/56 pass | root gate output | integration | 根仓治理控制面 |
| `rtk bash tests/test_effect_eval.sh` | 1 -> 0 | 首轮暴露 4 个 route/safety 缺陷；修复后 24/24 | `negative-results.md` | source/test | `effect_eval_contract.json`、inputs/labels |
| `rtk /tmp/adk-ci-tools/bin/ruff check ...` | 0 | Ruff 0.15.21 critical rules pass | CLI output | source/test | `pyproject.toml`、ADK Python core |
| `rtk bash scripts/devkit.sh security check --summary-json` | 0 | workflow pin、permission、secret/symlink checks pass | CLI output | source/test | `.github/workflows/*.yml` |
| `rtk bash tests/run_all.sh` | 0 | 51/51 PASS | `verify-report.md` | source/test | ADK full regression |
| `rtk bash scripts/devkit.sh benchmark run --iterations 5 ...` | 0 | 7 个 latency/I/O budget 与 peak-memory gate 全通过 | `benchmark.json` | source/test | `adk_performance_budgets.json` |
| `rtk bash scripts/devkit.sh eval effect ...` | 0 | route/safety/trace/outcome 100%，routing ablation delta 0.3333 | `effect-eval.json` | source/test | effect inputs/labels |
| `rtk bash scripts/check-official-docs-governance.sh --summary-json` | 0 | OpenAI/Anthropic 共 69 条 freshness record 通过 | `verify-report.md` | source/test | `official_docs_freshness_gates.json` |
| `PYTHONPATH=/tmp/adk-audit-tools pip-audit 2.7.3 --strict .` | 0 | 本机兼容版依赖审计未发现已知漏洞 | CLI output | source/test | `pyproject.toml` |
| `rtk scripts/check-all.sh --quick` | 1 | 52/56 PASS；4 项均为未提交 rc.2/rc.1 lock 同源边界 | `verify-report.md` | integration | 根仓 `adk.lock`、gitlink、scorecard |
