# Verification Evidence：adk-terminal-contract-hardening

- Scope：性能门禁、typed manifest、copy-only 安装合同、Python/依赖支持基线及其根仓集成。
- Claim：本地 source/test 实现已验证；未声明 release-ready、remote-CI-pass、runtime-certified 或 terminal-mature。
- Verifier：机械命令证据 + `review-findings.md` 独立复审。

| Command | Exit | Result summary | Evidence path | Layer | Artifact |
|---|---:|---|---|---|---|
| `rtk tests/test_product_maturity_contracts.sh` | 0 | 根包装器必须调用 strict timing checker；根产品合同通过 | `tests/test_product_maturity_contracts.sh` | Source Test | TC-001 |
| `rtk agent-dev-kit/tests/test_performance_budgets.sh` | 0 | 预算内 fixture 通过，999999ms 超预算 fixture 被稳定拒绝 | `tests/test_performance_budgets.sh` | Source Test | TC-001 |
| `rtk agent-dev-kit/tests/run_all.sh --quick --timing-json /tmp/adk-quick-terminal-final-3.json` | 0 | 16/16；65331ms | `/tmp/adk-quick-terminal-final-3.json`（会话临时证据） | Workflow Test | quick gate |
| `rtk agent-dev-kit/scripts/check-performance-budgets.sh --strict --timing-json /tmp/adk-quick-terminal-final-3.json --summary-json` | 0 | quick budget 120000ms；failure=0、warning=0 | 本文件中的命令记录 | Performance | quick strict |
| `rtk agent-dev-kit/tests/run_all.sh --timing-json /tmp/adk-full-terminal-current.json` | 0 | 当前最终树 53/53；340107ms | `/tmp/adk-full-terminal-current.json`（会话临时证据） | Workflow Test | full gate |
| `rtk agent-dev-kit/scripts/check-performance-budgets.sh --strict --timing-json /tmp/adk-full-terminal-current.json --summary-json` | 0 | full budget 600000ms；failure=0、warning=0 | 本文件中的命令记录 | Performance | full strict |
| `rtk scripts/check-adk-performance-ops.sh .` | 0 | 产品成熟度、benchmark、security、release、16 项 quick 与 strict timing 全部通过 | `scripts/check-adk-performance-ops.sh` | Workspace Integration | root performance |
| `rtk scripts/check-all.sh --quick` | 1 | 53/56；仅 current-status、Software M5 readiness、strict subrepo state 因未提交 candidate/旧 digest 失败 | `reports/terminal-closure-remediation-2026-07-18.md` | Workspace | pre-commit boundary |
| `rtk agent-dev-kit/scripts/devkit.sh benchmark run --iterations 5 --summary-json` | 0 | `manifest_validate` p95=99.853ms，7 个时延与内存 gate 全部通过 | `src/agent_dev_kit/model.py` | Performance | TC-002 |
| `rtk agent-dev-kit/tests/test_product_maturity_v3.sh` | 0 | copy-only、typed schema、支持基线、release/SBOM 负向与正向合同通过 | `tests/test_product_maturity_v3.sh` | Source Test | T2/T3 |
| `rtk agent-dev-kit/scripts/devkit.sh validate --strict` | 0 | Draft 2020-12 与跨字段/资产 strict 验证通过 | `manifests/manifest.schema.json` | Manifest | T2 |
| `rtk agent-dev-kit/scripts/devkit.sh security check --summary-json` | 0 | built-in security：0 failure、0 warning | `src/agent_dev_kit/quality.py` | Source Security | T3 |
| `rtk agent-dev-kit/scripts/devkit.sh release check --summary-json` | 0 | 3 个 direct target、1 个 external handoff，release contract pass | `src/agent_dev_kit/release.py` | Release Source | T3 |
| `rtk shellcheck -S error ...` | 0 | 本轮 shell 与全 ADK script/test error-level ShellCheck 通过 | 本文件中的命令记录 | Static | maintainability |
| `rtk scripts/check-all.sh --full` | 1 | 55/62；7 项初始失败中性能/goal 已修复，剩余派生于未提交 ADK、旧 rc.2 evidence digest 与严格 subrepo 状态 | `reports/terminal-closure-remediation-2026-07-18.md` | Workspace | open boundary |
| `rtk bash /home/leiwenjun/codex/scripts/final-ready.sh` | 0 | final-ready pass；session coach 的 CRITICAL/HIGH 信号来自长线程及 `~/codex` 既有 dirty 资产，本轮未修改或 apply 该目录 | 本文件中的命令记录 | Session Governance | final handoff |

## Controlled local CI parity

| Command | Exit | Result summary | Evidence path | Layer | Artifact |
|---|---:|---|---|---|---|
| `rtk scripts/run-local-ci-parity.sh --prepare --python all --mode quick` | 0 | 重建并核验 v2 工具镜像；Python 3.11/3.12 各 17/17，离线 gates、独立 audit、wheel 均通过 | `tools/local-ci/`、`scripts/run-local-ci-parity.sh` | Workflow | T6 / TC-005～TC-007 |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full` | 0 | source snapshot `33ab17d4...`；Python 3.11/3.12 各 54/54，performance/security/30-route eval/release/wheel/audit 全通过 | `ci-waiver.json` evidence refs | Workflow | T6 |
| `rtk docker image inspect ... agent-dev-kit-local-ci:python-3.11` | 0 | image `sha256:2f4ec1...`；contract v2、3.11 base digest、definition `663f5c72...` 一致 | `ci-waiver.json` | Environment | TC-007 |
| `rtk docker image inspect ... agent-dev-kit-local-ci:python-3.12` | 0 | image `sha256:3fcedbe...`；contract v2、3.12 base digest、definition `663f5c72...` 一致 | `ci-waiver.json` | Environment | TC-007 |
| `rtk docker run --rm --network none --user 65532:65532 --entrypoint id ...` | 0 | `uid=65532(adk-ci) gid=65532(adk-ci)` | `review-findings.md` | Permission | TC-006 |
| `rtk tests/test_product_maturity_v3.sh` | 0 | bounded fallback 与 repository-escaping symlink 不跟随读取回归通过 | `tests/test_product_maturity_v3.sh` | Source Security | TC-008 |

## Before / After

| Finding | Before | After |
|---|---|---|
| 根性能包装器假绿 | quick 150665ms 超过 120000ms，包装器仍可通过 | 包装器调用同一 strict checker，超预算返回非零 |
| quick 抖动 | final sample 154962ms，strict 正确失败 | 分层去除重复重型工作后 65331ms；预算未放宽，测试仍在 full/根包装层 |
| typed schema 性能 | `manifest_validate` p95 557.465ms > 500ms | 内容键控、容量 8 的 schema/validator cache；p95 99.853ms |
| install 漂移 | manifest 默认 symlink，installer 实际只支持 copy | JSON/YAML/schema/CLI/docs 统一 copy-only，symlink 继续 fail closed |
| 支持基线 | Python 3.8 与宽松 PyYAML 声明 | Python 3.11+；PyYAML/jsonschema 固定版本；doctor 结构化报告漂移 |

## 未执行/未通过边界

- 宿主机为 Python 3.8.10，且宿主 PyYAML/jsonschema 版本不满足新的发布基线；宿主 `doctor` 正确返回 fail。支持环境证据来自固定 Docker Python 3.11.15/3.12.13 与精确依赖版本，不把旧解释器结果冒充支持矩阵。
- Ruff 0.15.21、pip-audit 2.10.1、ShellCheck、wheel build 已在身份可核验的本地容器执行；GitHub Actions 未在本轮远程触发，本地 waiver 不替代远程 run URL、attestation 或 provenance。
- manifest 改变后，旧 `3.1.0-rc.2` rehearsal digest 依法失效；必须在 owner 决定版本、提交后重建候选证据，不能改写旧证据。
- 未 commit、push、tag、apply `~/codex`/`~/.codex`，未运行付费 runtime campaign，也未生成 field certification。
