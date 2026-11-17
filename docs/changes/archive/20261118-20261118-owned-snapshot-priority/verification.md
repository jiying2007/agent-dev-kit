# 源码验证：20261118-owned-snapshot-priority

## 精确来源与执行边界

基线021d81aa4923dbc68a934d9cd0d64c4dfed76167；最终产品候选64d120ebcbc5d77fd90af99bac2bb9f4f3a13682，tree35a666c2b4349b1890f5788241ac32bcf8080e38；版本11.4.2。只改变既有测试helper及验收、九个版本/变更日志投影，共十文件。最终helper SHA256为2be3cbba83ee965bdba635fc5e5d30263e6ecce7f694a1e9c75833b8a39be295。

实现者ai/implement-snapshot-priority；coordinator负责需求/设计、版本和证据编排；ai/independent-review只读实现。独立反例OSP-1/OSP-2及原main失败均保留，不把中间模块通过当最终质量裁决。前两候选的full在发现major后实际中止，exit130，不计通过。

## 已完成的命令级证据

| 层级/关联 | 命令或控制 | 退出码/结果 | 原件 |
|---|---|---|---|
| TASK-001 / 原发现缺陷 | 固定256无关前缀，fake-proc与真实Ninja原验收 | exit1；2tests/3failures，RED | evidence/implementation/red-foreign-prefix/result.json.json |
| TASK-001 / 能力边界 | 真实bash/Ninja/sh/leaf的stat/task/children观察 | 4个children均ENOENT；不推断hosted原因 | evidence/implementation/real-children-capability.json.json |
| TASK-001 / 首版负结果 | tree优先但缺children时的相同真实前缀 | exit1；2subTest失败；目录名green-foreign-prefix不改变实际失败 | evidence/implementation/green-foreign-prefix/result.json.json |
| OSP-1 | 第256/512条numeric PID、两fresh pass | 原RED后同文本GREEN；不增加256上限 | evidence/boundary-revision/implementation-verification.json.json |
| OSP-2 | 实际跨批17PID与17批日志累计截断 | 原2fail后同文本2/2GREEN；fresh清理继续、资格unverified | evidence/report-cap-revision/implementation-verification.json.json |
| 最终模块 | `python -m unittest -v tests.test_skill_command_examples` | exit0；66/66、0skip，25项runner及原ADC/CMake | evidence/report-cap-revision/module-final/result.json.json |
| 最终定向质量 | `python -m ruff check tests/test_skill_command_examples.py`；`git diff --check` | 均exit0，同一源码摘要 | evidence/report-cap-revision/ruff-final/result.json.json；diff-check/result.json.json |
| 独立缺陷复查 | 两原collector仅更换候选/摘要/输出绑定，核心反例不变 | 原缺陷oracle均exit1/not-confirmed，原结果保留 | evidence/independent/final-revision-64d120/cursor-boundary-counterexample-result.json.json；accumulated-report-cap-result.json.json |
| 独立恢复与真实进程 | recovery_and_real_probe.py | exit0；OSP-1/2恢复，真实Ninja/线程leaf/foreign会话，rescue_signal_pids为空 | evidence/independent/final-revision-64d120/recovery-and-real-result.json.json |
| 生命周期verify | strict、format、change-governance | 实际exit0；首次负结果section格式失败另保留 | verify-report.md |
| 精确候选静态/契约 | Ruff、focused Ruff、mypy32文件、format、strict、release-check、core export | 七阶段均exit0，导出5agents/22skills | evidence/full/results.json.json |
| 精确候选full | `bash tests/run_all.sh --timing-json ...` | exit0；102/102，timing410588ms | evidence/full/full-timing.json.json |

最终模块实际UTC为2026-11-17T17:10:51.830617至17:11:01.177017，unittest9.199s、进程9.346407570s。原real-Ninja方法、三个身份授权函数及之前验收均逐字保留；完整控制映射见各implementation-verification原件，不以口头陈述代替摘要。

独立组合探针实际UTC为17:13:14.999417–17:13:16.527131Z；只注入根procfs枚举顺序，真实stat/pidfd/信号保持。fixture收尾前launcher与leaf均已不存在，foreign身份保持且存活，无补杀。首次缺既有工具链PATH的precondition失败另保留，当时真实fixture未启动。独立原件21份与index均逐字核验后包装，见evidence/independent/index.json。

## 完整验证状态

独立source walkthrough和最小负控制于17:13确认无未解决major后，才开始本候选完整验证。在新的洁净detached worktree、外置CPython3.12.14工具链运行；八阶段全部exit0，full102/102。1082个运行输入在source-before/source-after逐文件一致，HEAD/tree与tracked clean保持。后续change证据和review/archive属于另行审查的包装，不冒称已经包含在该次full的Git tree。

full实际UTC为2026-11-17T17:13:37.985541Z至17:20:28.694200Z，进程410.708667527s，runner timing410588ms；source-after完成于17:20:28.748185Z。原full日志SHA256为0d1bee4e82001511f12291d9c3be0867228a5a396f58b49d3acd176ef3eed61e。紧凑runner对成功组只打印名称，因此该日志内容可与其他全通过运行相同；本次身份以实际UTC、timing、精确commit/tree及前后源摘要共同绑定，不以该log hash独占身份。

13份full原件保留于evidence/full/index.json；source/模块/RED/独立反例和两个中止运行分别保留原字节及摘要。format保留既有非可执行脚本warning，结果仍exit0；release-check记录runtime_eval_executed=false。

## 资格限制

原11.4.0两次ADC/CMake15秒等待和11.4.1主线bounded具体原因均保留UNKNOWN。新反例证明源级缺口，不补写旧宿主原因。默认work15秒、cleanup总截止1秒，每批50ms/256 discovery entries及累计16records保持；主动另建SID的任意逃逸不是此有限helper保证。

未执行付费模型、Token/费用收益评测、live宿主安装、设备或当前M5；Provider/宿主能力缺失保持UNAVAILABLE。未来PR/main CI、不可变Release和Root source-only必须取得各自真实回执；源码阶段不预认证。正常lifecycle verify只覆盖其实际strict/format/governance命令，完整产品回归与独立canonical另行绑定。
