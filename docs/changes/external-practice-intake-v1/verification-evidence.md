# Verification Evidence：external-practice-intake-v1

- Scope：统一七来源 external-practice intake、reference-repository 生命周期硬切、ADK Agent/optional Skill/Workflow 与 RC4 版本/回退合同。
- Claim：ADK source、release artifact/rehearsal、root integration 与独立复审均已验证；本地 source 范围达到终态闭环。未声明 source-to-live、remote CI、publish、Software M5 certification 或 field completion。
- Source commit：`ecec9185e44fe7389fc82640e563643954e7ec2d`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tests/run_all.sh --fail-fast --timing-json /tmp/adk-external-practice-rc4-full.json` | 0 | ADK full 54/54，351240ms | `/tmp/adk-external-practice-rc4-full.json`（临时） | ADK Test | T4/T6 |
| `rtk bash scripts/devkit.sh validate --strict` | 0 | JSON/YAML/schema/asset/profile/workflow strict validation pass | `manifest.json`、`manifest.yaml` | ADK Manifest | T4 |
| `rtk bash scripts/devkit.sh security check --summary-json` | 0 | failure=0、warning=0；Git inventory 708 files | `src/agent_dev_kit/quality.py` | ADK Security | T4/T6 |
| `rtk bash scripts/devkit.sh benchmark run --iterations 5 --summary-json` | 0 | 7 个 latency gate 与 peak-memory gate 全部通过 | `manifests/adk_performance_budgets.json` | ADK Performance | T6 |
| 两次 `release build --version 3.1.0-rc.4` + `cmp` + `sha256sum -c` | 0 | 从 `ecec918` archive 两次构建字节一致；587 files；SHA256 `34ffba31...cbc706d` | `/tmp/adk-rc4-release-final.dBIxcu/`（临时） | Release | T6 |
| `release rehearse --previous-artifact ...rc.3 --candidate-artifact ...rc.4` | 0 | RC3/RC4 各安装 39 项；rollback removed/restored=39 | `release-rehearsal.json` | Release Runtime | T6 |
| `rtk scripts/practice-intake.sh collect --provider gitee ... --allow-network` | 2 | live endpoint 返回空；按合同记录 `degraded-empty`，非 clean pass | `/tmp/gitee-agent-evidence.json`（临时） | Live Read-only | T2/T3 |
| `rtk scripts/practice-intake.sh check --kind evidence --input /tmp/gitee-agent-evidence.json` | 0 | live Gitee evidence schema、边界与 ledger hash 通过 | `/tmp/gitee-agent-evidence.json`（临时） | Root Contract | T3 |
| `rtk proxy /usr/bin/time ... practice-intake.sh cycle ...` | 0 | 七 provider fixture cycle：7 candidates；0.11s；max RSS 17592KiB | `/tmp/external-practice-bench-evidence.json`（临时） | Root Performance | T3/T6 |
| `rtk scripts/check-software-m5-readiness.sh . --summary-json` | 0 | integrity/declaration pass；RC4 m5-ready；certified=false | `manifests/software_m5_policy.json` | Root M5 Boundary | T6 |
| `rtk scripts/check-all.sh --full`（pre-sync） | 1 | 53/58；`adk_lock/current_status/subrepo_state` 三个未同步事实派生出 evidence bundle/workspace entrypoints 共 5 项失败；其余功能/安全/性能门禁通过 | 本文件与终端证据 | Root Pre-commit | T6 boundary |
| `rtk scripts/check-all.sh --quick`（final integration） | 0 | root quick 53/53 | `reports/adk-v3-1-rc4-release-evidence-2026-07-19.json` | Root Test | T6/T7 |
| `rtk scripts/check-all.sh --full`（final integration） | 0 | root full 58/58；fail=0 | `reports/adk-v3-1-rc4-release-evidence-2026-07-19.json` | Root Test | T6/T7 |
| `rtk bash scripts/check-current-status-consistency.sh . --summary-json` + positive/negative fixture | 0 | last-verified、mapped-change 与 pending live 声明一致；漂移负例 fail closed | `reports/current-status.md`、`tests/test_current_status_consistency.sh` | Root Status | T7 |
| `knowledge-capture.sh ... --status reviewing --apply` | 0 | candidate 已事务登记；`active_promotion=false`、`memory_write=false` | `domains/codex/archive/codex-archive/research-notes/20260719-llm-agent-external-practice-intake-terminal.md` | Knowledge Hub | T7 |
| `knowledge-orphan-files.sh --all --strict --json` | 0 | 361 个长期正文覆盖完整；新增 archive inventory count/hash 已显式复核 | `registry/body-coverage.json` | Knowledge Hub | T7 |
| `knowledge-search.sh llm-agent-external-practice-intake-terminal-20260719 --status reviewing --json` | 0 | exact-id 命中 1 条 reviewing candidate | Knowledge Hub local index | Knowledge Hub | T7 |
| `knowledge-check.sh --dry-run --json --diagnostics` | 1 | 本次 candidate error=0、body coverage=ok；Hub 全局仍有 199 条与本 change 无关的既有 frontmatter 漂移 | Knowledge Hub diagnostics | External Boundary | T7 boundary |
| `rtk ruff check ...` | not-run | 当前环境没有 ruff；未临时安装或伪报 | `negative-results.md` | Static Negative | T6 |

## 本地闭环与外部边界

- root quick/full、current-status、hard-cut residue、release rehearsal 与独立 review 已通过；blocker=0、major=0、minor=1（非阻塞拆包建议）。
- Knowledge Hub candidate 已 capture 为 `reviewing`，可精确检索且 strict body coverage 通过；Hub 全局 199 条既有 frontmatter 漂移不由本 change 修改或掩盖。
- source-to-live 因 mapped Agent/Skill/Workflow 发生变化而保持 `required-pending-owner-authorization`；本 change 不写 `~/codex` 或 `~/.codex`。
- remote CI、tag、push、publish、双 runtime campaign 和 field evidence 均未执行。
