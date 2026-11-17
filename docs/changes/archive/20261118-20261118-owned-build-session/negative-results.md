# 负结果记录：20261118-owned-build-session

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-11-17T15:35Z起 | main第一次全量可交付 | run44116100760 attempt1 | 101/102；ADC/CMake原15秒超时 | 未发布，下游停止，原件摘要保留于#282 |
| 2026-11-17T15:51Z起 | 唯一预注册同源复验 | 同run attempt2 | 101/102；同用例再次超时 | STOP_NO_FURTHER_RETRY，不再重跑旧main |
| 2026-11-17T16:07:48Z | 外组清理等于session清理 | 一次真实Ninja 0.2s合成超时 | helper称complete而两个异PGID后代仍活 | 已证实helper缺陷，不证明原15秒根因 |
| 2026-11-18 +08:00 | 有可引用历史lesson | rg knowledge/L2-domain/lessons.md | 文件不存在，exit2 | 不伪造命中，既有历史超时仍unknown |
| 2026-11-17T16:13:55Z | 原helper能覆盖Ninja新组 | 新真实Ninja验收，旧helper | exit1；1test/2subtest失败，漏快照且leaf仍活 | 原RED完整保留，验收函数原文未弱化 |
| 2026-11-17T16:17:33.940629Z | 首版所有诊断异常均保留timeout | 晚期状态读异常新回归 | exit1，RED：异常覆盖原timeout | 最终版修复该分支；原RED及中间GREEN均保留 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rg -n -i 'ninja|cmake|timeout|子进程|进程组' knowledge/L2-domain/lessons.md` | 2 | lesson文件不存在 | 本表 | read-only | proposal.md |
| `python -m unittest tests.test_skill_command_examples.CommandExampleRunnerTests.test_real_ninja_child_group_is_observed_and_cleaned_without_touching_another_session -v` | 1 | 真实基线RED，两项验收失败 | evidence/implementation/red-ninja/result.json.json | L2 | requirements.md ACC-001/002 |
| `python -m unittest tests.test_skill_command_examples -v` | 0 | 最终52/52、0skip，unittest8.175s | evidence/implementation/green-module-final/result.json.json | L2 | requirements.md ACC-001/002/003 |
| `python -m ruff check tests/test_skill_command_examples.py` | 0 | 最终lint通过 | evidence/implementation/ruff-final/result.json.json | L2 | tasks.md TASK-001 |
| `bash tests/run_all.sh --timing-json ...` | 0 | 洁净5ff076a完整102/102，1082源输入无漂移 | evidence/full/summary.json.json | L3 | tasks.md TASK-002 |
| 原Ninja probe原字节单次运行 | 1 | 原oracle的not-confirmed保留，实际已无live后代且快照完整 | evidence/independent/original-counterexample/ninja-cleanup-probe-result.json.json | independent | requirements.md ACC-001/002 |
| 独立run_independent_probes.py | 0 | 实际pidfd、身份/外会话/缺能力负控制成立 | evidence/independent/probe-result.json.json | independent | requirements.md ACC-002/004 |
| `bash scripts/devkit.sh verify --change 20261118-owned-build-session --owner leiwenjun` | 0 | 既有治理/strict/format实际通过 | verify-report.md | governance | proposal.md VERIFY-001/002/003/004 |

所有原日志与源快照均以可逆JSON包装保留原字节、长度和SHA256；包装不会改变原exit或RED/GREEN意义。主线两次失败与原ZIP分别见evidence/baseline/index.json。晚期异常的精确实际UTC以red-late-status/result.json.json原件为准，不将修复后的通过覆盖中间版本结果。
