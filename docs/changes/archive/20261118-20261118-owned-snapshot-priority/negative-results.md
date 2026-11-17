# 保留的负结果

## 已验证的负结果

| 时间（UTC） | 假设/方案 | 验证方法 | 结果 | 处置 |
|---|---|---|---|---|
| 2026-11-17T16:43Z | 11.4.1主线可交付 | run44128721869 attempt1 | Ninja快照bounded/空、leaf仍S，full101/102 | 发行停止，原件保留，不重跑 |
| 2026-11-17T16:54Z | 全局前缀不影响自有发现 | 固定256无关条目、旧helper | 两测试三项失败 | 实际RED，验收保持 |
| 2026-11-17T16:55Z | 只做tree优先足够 | 同一真实Ninja前缀 | 两项失败，真实children接口缺失 | 原1秒内增加有界cursor续扫 |
| 2026-11-17T17:04Z | 每批推进不会丢条目 | 独立第256numeric counterexample | fresh pass重复漏读PID9000 | OSP-1修复，原full中止130 |
| 2026-11-17T17:07Z | 每批observed足以complete | 独立17PID累计报告反例 | report截断而cleanup complete | OSP-2修复，第二full中止130 |
| 2026-11-17T17:14:32Z | 现有负结果列表满足治理格式 | devkit verify | exit1，缺必需表格section | 原报告先保留，再补既有要求格式 |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rg -n 'procfs|snapshot|256|Ninja|进程|超时' knowledge/L2-domain/lessons.md README.md` | 2 | lesson文件不存在，README有匹配，不伪造历史经验 | 下述原观察 | read-only | proposal.md |
| `python -m unittest -v` 固定前缀两个完整用例名见原record | 1 | 2tests/3failures，原RED | evidence/implementation/red-foreign-prefix/result.json.json | L2 | ACC-001/003 |
| `python probe_children.py` | 0 | 真实四进程children文件ENOENT；只说明本地能力 | evidence/implementation/probe-real-children/result.json.json | read-only | design.md |
| 边界回归定向命令，完整argv见原record | 1→0 | 第256/512项及fresh pass从RED变GREEN | evidence/boundary-revision/implementation-verification.json.json | L2 | OSP-1/ACC-002 |
| 累计报告截断定向命令，完整argv见原record | 1→0 | 17PID/17批两个实际截断验收RED→GREEN | evidence/report-cap-revision/implementation-verification.json.json | L2 | OSP-2/ACC-002 |
| `python -m unittest -v tests.test_skill_command_examples` | 0 | 最终66/66、0skip，25runner | evidence/report-cap-revision/module-final/result.json.json | L2 | TASK-001 |
| `python -m ruff check tests/test_skill_command_examples.py` | 0 | 最终源码lint通过 | evidence/report-cap-revision/ruff-final/result.json.json | L2 | TASK-001 |
| `git diff --check` | 0 | 最终源diff格式通过 | evidence/report-cap-revision/diff-check/result.json.json | L2 | TASK-001 |
| 旧955d完整验证编排，随后Ctrl-C | 130 | 因OSP-1中止，不称full PASS | evidence/rejected-full/interruption.json.json | L3 | TASK-002 |
| 旧4f94完整验证编排，随后Ctrl-C | 130 | 因OSP-2中止，不称full PASS | evidence/rejected-boundary-full/interruption.json.json | L3 | TASK-002 |
| `bash scripts/devkit.sh verify --change 20261118-owned-snapshot-priority --owner ai/coordinator` 首次 | 1 | 缺负结果必需section；不是产品测试失败 | evidence/verify-format-failure/verify-report.md.json | governance | VERIFY-001/002/003/004 |
| 原两缺陷collector的新来源绑定副本 | 1 | 原旧缺陷oracle not-confirmed，不改标脚本PASS | evidence/independent/final-revision-64d120/cursor-boundary-counterexample-result.json.json；accumulated-report-cap-result.json.json | independent | OSP-1/2 |
| 独立recovery_and_real_probe.py | 0 | 恢复oracle及真实Ninja/线程leaf/foreign控制通过，无rescue信号 | evidence/independent/final-revision-64d120/recovery-and-real-result.json.json | independent | ACC-001/002/003 |
| `bash scripts/devkit.sh verify --change 20261118-owned-snapshot-priority --owner ai/coordinator` 格式修正后 | 0 | 既有strict/format/governance通过，未替代full | verify-report.md | governance | VERIFY-001/002/003/004 |
| `bash tests/run_all.sh --timing-json ...` 最终64d120e | 0 | 102/102、410588ms；1082源输入一致 | evidence/full/summary.json.json | L3 | TASK-002 |

## 原观察与边界

- 11.4.1 main021d81aa/run44128721869 attempt1：Ninja两个subTest失败，snapshot bounded/[]、leaf4727仍S，work1.001s/cleanup0.005s、session-unverified。原日志61503bytes SHA256 67a7e53456a9efdbe275254aa005da3bc5ce7d3eb1ca0a1cecab41edbfa79a95；ZIP14350265141 SHA256 66efddb4dfe29340392b26e1bb9ed771c0f01301f842166faf43d76d513fce9b。具体bounded原因未记录，UNKNOWN；不自动复跑。
- 11.4.0 main15fa/run44116100760两次ADC15s超时仍失败，唯一预注册复验已耗尽；原因UNKNOWN，原件见前次归档，不重写。
- knowledge/L2-domain/lessons.md不存在，实际rg exit2，不称命中经验。
- 恢复时试探devkit workflow --help实际exit2；帮助指示直接propose/apply/verify/review/archive，随后使用既有入口，无产品变更。
- 首次文档apply_patch因同路径delete/add不支持而原子拒绝；未部分应用。随后以Update重做，不绕过工具。
- 新RED/GREEN与审查发现按实际运行增补，不预填成功。
- 候选955d982/helper408ef93e虽完整模块63/63通过，但独立review于17:04:06Z确认global cursor在第256个numeric条目发生双计数、advance后未读stat，fresh pass同位置重复遗漏。原counterexample和result保留；该候选不能取得Spec/Quality PASS。
- 该候选full于17:02:45.729496Z开始，在上述major确认后主动Ctrl-C，工具实际exit130。前七阶段通过仅限此候选；full中止不能称通过，也不复跑同head。修正后新提交在新目录运行完整验证。
- OSP-2：独立fake-proc/信号ack探针在955d与新4f94/e622复现，多个各自observed批次合计17个ownedPID使累计report变bounded/records_truncated，而cleanup仍complete。最终fake成员已Z/消失，因此仅认定状态契约缺陷，不称活进程漏杀。4f94于17:06:45.067408Z开始的full再次主动Ctrl-C，工具实际exit130；不计通过。
- 执行次序调整：先完成完整源码审查和已证实major的定向修复，再对最终冻结候选运行full；旧部分运行和所有失败原件保留。
- OSP-1作者新增第256/512位置与两fresh pass验收，17:05:29Z旧源码实际1test/2subfail，17:05:45Z同文本GREEN；64/64模块通过的4f94仍因OSP-2阻断，不能把该模块通过当完整审查通过。
- OSP-2作者新增实际fake-proc跨pass累计17PID与17批日志截断验收，17:09:07Z旧源码2fail；17:09:19Z同文本2/2GREEN。最终64d120e/helper2be3的完整模块66/66、0skip、Ruff/diffcheck实际通过；完整回归/独立最终裁决/外部发行另行证实。
- 16:54:03.962658–16:54:05.127794Z固定前缀RED：2tests/3failures，原source326309d4…；fake-proc漏9000–9003，真实Ninja原验收漏采/存活两个subTest失败。
- 16:55:00.037338–16:55:01.177483Z首版修复仍exit1/2failures，fake-proc通过但真实Ninja前缀仅发现leader；目录虽名green-foreign-prefix，其实际结果始终记录为失败，不能称GREEN。source a7a8cb66f3599ed27cf495439e37b9b6d7c7a40550357ce9481d53231d1bcbce。
- 16:55:32Z真实proc能力探针：bash/Ninja/sh/leaf的stat/task可用但各children文件ENOENT；设计增加原1秒内有界续扫，不skip、不伪造接口、不提高预算。第一次探针缺venv PATH导致ninja=None/Popen前TypeError，未起进程；正常环境的单次真实观察另存，不覆盖第一次记录。
