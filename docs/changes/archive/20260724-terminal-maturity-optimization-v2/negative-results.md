# 负结果记录：terminal-maturity-optimization-v2

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-23 | 根 `check-all --full` 已覆盖全部回归 | full + root tests 枚举 | full 52/58；15 个根测试仅 13 个通过，且无统一 runner | 聚合不能证明测试完整性 |
| 2026-07-23 | architecture 正向 fixture 与 checker 一致 | 单跑 `test_architecture_reports.sh` | fixture `reports=0`，缺 maturity audit/scorecard/registry | fixture 已漂移 |
| 2026-07-23 | 宿主 full 通过即可证明发布 Python 基线 | doctor + Docker parity | 宿主 Python 3.8 doctor fail；Docker 3.11/3.12 quick pass | unsupported host 不能冒充发布证据 |
| 2026-07-23 | 直接续期 dirty baseline 可恢复门禁 | subrepo/triage checks | 三个 baseline 过期且存在 655/115/216 项变化 | 未审查前续期会掩盖漂移 |
| 2026-07-23 | `context-preflight.sh --help` 是只读 help | 运行 help | 把 `--help` 当路径并失败 | 属于 `~/codex` 外部仓，记录但不越界修复 |
| 2026-07-23 | ADK CLI 存在 `format-check` 子命令 | `rtk bash scripts/devkit.sh format-check` | exit 2，命令不存在 | 改用权威入口 `rtk bash tests/test_format.sh`，后者通过 |
| 2026-07-23 | change verify 失败后可直接修复并重试 | 首次 `devkit.sh verify` | checklist 精确标签失败后进入 `verify-failed`，原状态机禁止重试 | 将 `verify-failed` 设为显式重试状态并增加回归，不手改 state |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash scripts/check-all.sh --full` | 1 | 52/58；6 failures | terminal audit output | Workflow | proposal |
| `rtk bash agent-dev-kit/tests/run_all.sh` | 0 | 56/56 | terminal audit output | Workflow | proposal |
| root `tests/test_*.sh` enumeration | 1 | 13/15 | terminal audit output | Test | proposal |
| `rtk scripts/run-local-ci-parity.sh --python all --mode quick` | 0 | 3.11/3.12 各 19/19，audit clean | Docker snapshot `f0215482...` | Workflow | proposal |
| `rtk bash tests/run_all.sh --timing-json docs/changes/terminal-maturity-optimization-v2/adk-full-timing.json` | 0 | 57/57；3 个慢测试被结构化标记 | `adk-full-timing.json` | Test | T4/T7 |
| `rtk bash tests/test_format.sh` | 0 | format pass | terminal output | Test | T4 |
| `rtk scripts/classify-repo-worktree.sh . <repo>` | 0 | 655/115/216；fingerprint 与分类全部匹配 | root triage report | Source | T6 |
| `rtk scripts/check-reference-dirty-triage.sh . --date 2026-07-23 --summary-json` | 0 | pass，3 items | `../reports/reference-dirty-triage-2026-07-23.json` | Workflow | T6 |
| `rtk bash scripts/devkit.sh verify --change terminal-maturity-optimization-v2` | 1 | checklist 缺精确 Prompt 标签；进入 verify-failed | `verify-report.md` | Workflow | T7 retry-1 |
