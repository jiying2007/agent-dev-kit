# Negative Results

## 已验证的负结果

| 时间 | 尝试 | 结果 | 决策 |
|---|---|---|---|
| 2026-08-02 | 在未提交 ADK 工作树运行 root `--release-clean --smoke` | 10/12；`subrepo-state` 与 evidence bundle 因 ADK dirty 失败 | 不放宽门禁，建立 RC7 exact-commit baseline |
| 2026-08-02 | 在宿主 Python 3.8 运行 ADK release check | 功能 pass，但明确标记 development-only | 发布证据只使用 pinned Python 3.11/3.12 local-CI |
| 2026-08-02 | RC7 定向 release check 首轮 | `.version-lock` 仍为 rc.6，release/Software M5 fail closed | 同步 lock 到 rc.7 后复跑，不绕过版本一致性 |
| 2026-08-02 | RC7 change governance 首轮 | proposal 缺固定标题 `问题陈述（单问题）` | 修正工件结构后复跑，不弱化治理检查 |
| 2026-08-02 | exact source `e03898f` Python 3.11 full parity 首轮 | `test_docs_cli_alignment` 发现 `task-cost` 缺一等命令章节 | 废弃该 source 的 artifact `38c6a14b…cf59`，补文档后创建新 source commit 并从头验证 |

后续失败按命令、退出码、结果摘要、证据路径、层级和关联工件追加；不删除负结果。

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk scripts/check-all.sh --smoke --release-clean` | 1 | 10/12；ADK dirty 派生两项失败 | `/tmp/llm-agent-release-clean-smoke-20260802.json` | Root/Release | proposal |
| `rtk scripts/devkit.sh release check --summary-json`（首轮） | 1 | `.version-lock` 与 rc.7 不一致 | command output | ADK/Release | version identity |
| `rtk scripts/check-change-governance.sh docs/changes/rc7-token-context-release-baseline-2026-08-02`（首轮） | 1 | proposal 固定章节缺失 | command output | ADK/Workflow | proposal |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full`（source `e03898f`） | 130 | Python 3.11 后段由 docs/CLI alignment 阻断后主动终止 | command output | ADK/Test | T4 negative |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full`（source `60c9a9e`） | 0 | Python 3.11.15/3.12.13 各 58/58，dependency audit 无已知漏洞 | `verify-report.md` | ADK/Test | T4 |
| `rtk cmp out-a/...tar.gz out-b/...tar.gz` | 0 | 两次构建字节一致，SHA256 `a46d26d7…48e0` | `verify-report.md` | ADK/Release | T5 |
| `rtk sha256sum -c agent-dev-kit-3.1.0-rc.7.tar.gz.sha256`（A/B） | 0 | 两份 checksum 均为 OK | `verify-report.md` | ADK/Release | T5 |
| `rtk scripts/devkit.sh release rehearse --previous-artifact ...rc.6... --candidate-artifact ...rc.7...` | 0 | upgrade/rollback pass，39 项移除并恢复；远端发布不在范围 | `release-rehearsal.json` | ADK/Release | T6 |
| `rtk git diff --quiet 60c9a9e -- agents skills optional-skills workflows templates` | 0 | release source 到 evidence 工作树的 mapped asset diff 为空 | `verify-report.md` | ADK/Release | T7 |
