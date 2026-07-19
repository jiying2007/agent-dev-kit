# Verification Evidence：external-practice-intake-v1

- Scope：统一七来源 external-practice intake、reference-repository 生命周期硬切、ADK Agent/optional Skill/Workflow 与 RC4 版本/回退合同。
- Claim：ADK source、release artifact 和 rehearsal 已验证；root integration 正在收口；未声明 source-to-live、remote CI、publish、Software M5 certification 或 field completion。
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
| `rtk ruff check ...` | not-run | 当前环境没有 ruff；未临时安装或伪报 | `negative-results.md` | Static Negative | T6 |

## 当前未闭环项

- root quick/full 与 final current-status 尚待 ADK evidence commit、gitlink/lock/status 同步后执行。
- source-to-live 因 mapped Agent/Skill/Workflow 发生变化而保持 `required-pending-owner-authorization`；本 change 不写 `~/codex` 或 `~/.codex`。
- remote CI、tag、push、publish、双 runtime campaign 和 field evidence 均未执行。
