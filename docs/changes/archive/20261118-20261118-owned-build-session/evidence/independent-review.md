# 独立源码审查：20261118-owned-build-session

## 裁决与身份

**Spec：PASS。Quality：PASS。无未解决的 blocker / major。**

审查者为 `ai/independent-review`，独立于 helper 实现作者 `ai/implement-session-cleanup`。Coordinator 负责需求/设计、九项版本投影和证据整合；本审查者未修改被审实现、测试、需求或设计。Owner-delegated AI 授权以仓库既有 policy 为准，本记录不表示人类审查。

- 基线：`15fa31d1a3f994a516d5a9003edaadd1295c74b5`。
- helper 实现：`22c2dc2b6d398e49afee675f339040ff612a271e`。
- 完整受测产品：`5ff076a14c88c65132e44dd8bfdb4c2ab71ee4f8`。
- tree：`14e5482c9ea3f97abe6abfcc74f8251088e46e8e`。
- helper SHA256：`a17791efaf2ad0dd7b0923dc49b4c219df0a3eb563495b419cc9de281cb12fc0`。
- 完整累计原 patch：25,517 bytes，SHA256 `449e51ce95bb20f51ea51faaeda3ebc3aac77b957727e129fb2883a7a9b00b27`；已独立用 `git diff --binary <base> <head>` 重建并逐字节一致。
- 冻结审查输入：`review-input-state.json`，实际 captured_at 为 2026-11-17T16:28:19.119577Z。审查、记录和 validator 的后续实际时间由 canonical 与执行原件分别记录，不倒填时间。

## 审查范围与判断依据

完整产品 diff 为十个文件：一个既有测试 helper 文件，以及九项 11.4.1 元数据/变更日志投影。已检查原始 diff、最终文件、真实 RED、最终 module/Ruff、完整回归、独立探针和新增证据包装。ADC/CMake 示例、原默认预算、CI 门禁、固定评测输入和 grader 没有变化；评测计划只同步未执行 candidate 的版本标识，不构成新的评测结果。

本变更修复已单独复现的 timeout helper 缺陷。原 hosted main `15fa31d1` 的两次 ADC/CMake 15 秒等待仍为 **UNKNOWN**，不在本次 fixed findings 中。修复分支在工作超时后执行，无法把同一次已经超时的工作改判成功；新 head 的本地通过不能证明原等待根治。

### Spec 对照

| 验收 | 实际核对 | 判断 |
|---|---|---|
| ACC-001，自有 SID 的不同 PGID 后代进入限定快照 | `process_status` 解析 PID/PPID/PGID/SID/starttime/CPU/state；`owned_process_snapshot` 按 SID 筛选，仅读取 stat 与 wchan。原样独立 Ninja probe 的 sh/leaf 进入快照，无关 session 排除 | 满足 |
| ACC-002，身份核对、无误杀、清理真实性 | 未主动 reap 的 Popen leader 保留身份锚；pidfd 打开后再核 PID/SID/starttime，信号发往该 descriptor。身份漂移、权限/能力缺失、缺测或截断均保守返回；实际无关 session 控制保持存活 | 满足 |
| ACC-003，原预算、失败与双流 | 默认工作 15s；初始身份读取计入同一工作截止；清理共享原 1s；单次快照 50ms/256 entries/16 records 不变。晚期读取异常不覆盖原 timeout，不阻断原外组有界 fallback；正常退出/双流控制通过 | 满足 |
| ACC-004，真实 RED→GREEN、负控制、共享 helper 回归与独立审查 | 原 Ninja 新验收出现两项真实失败；晚期状态读取出现单独真实 RED；最终 52/52 module、0 skip，独立原样探针和实际 pidfd 负控制通过，最终 full 102/102 | 满足 |

### Quality 对照

`cleanup_owned_session` 不再把外层管道 EOF 当作整个 session 已退出的证明。它终止经过身份核对的成员，再扫描 live 成员；任何观测降级会阻止 complete。leader 在清理阶段不主动回收，fallback 仅针对原外组；若观察到替换身份则拒绝该组信号。随后双流未排空或 leader 未回收会进一步降低结果。没有新增依赖、runtime 控制面或产品公共 API。

pidfd 将信号绑定到已打开的进程，避免纯数字 PID 被复用后误指其他进程；它不被表述为任意恶意进程树隔离。主动再次 setsid 离开自有 SID 的进程仍在明确范围外。诊断受限时，保守的 unverified/incomplete 是允许结果，不能据缺测推导清理成功。

源码没有通过增加 ADC 时间、换生成器、减优化、跳过用例或修改门禁取得通过。九项元数据变更准确声明这是 helper 修复，保留旧 hosted 失败及尚待实际发行回执的边界。

## Findings

### OS-1：外层 PGID 漏采、漏清理且误报 complete — major，fixed

基线 helper 只观察和 SIGKILL 外层 PGID；真实 Ninja 普通规则创建不同 PGID、保留原 SID。原反例在 helper 返回 complete 后仍有活 sh/leaf，且其私有管道不必保持 Python 外层管道开启。

最终实现按自有 session 观察和清理，并以真实 pidfd/身份复核限制信号。独立原样 0.2s 反例观测到四个成员（bash、Ninja、新 PGID 的 sh/leaf）；原 timeout 保留，cleanup 实测 0.002s；返回后 leaf 不再存活，实验驱动器没有执行补杀。原始失败与修复后的独立观察分别保留。

### OS-2：首版晚期状态读取异常覆盖原 timeout — major，fixed

首版在 fallback 身份读取处未封装非 OSError 异常。实现者新增真实进程配合窄异常注入，先得到 exit 1 / RuntimeError，保留原 RED。最终版对该诊断读取异常降级为 session-unverified，同时继续由未回收 Popen 约束的原外组 fallback，保留原 timeout 和已有输出。最终 module 中该回归实际通过；相关 diff 已独立核对。

**本次没有新增未解决的源码 finding。历史 hosted ADC 等待仅作为范围外已知限制保留，不标 fixed。**

## 实际验证与证据

| 验证 | 实际结果与限定 |
|---|---|
| 实现者真实 Ninja 基线 | 1 test / 2 subtest failures，exit 1，旧 helper 漏快照且 leaf 活着；原输入与源码快照保留 |
| 实现者晚期读取 RED | exit 1，RuntimeError 覆盖原 timeout；随后修复，原件保留 |
| 最终完整 example module | 52/52，0 skip，unittest 8.175s；含 11 项 runner 控制与原 ADC/CMake |
| 最终单文件 Ruff | exit 0；helper 前后 SHA 均为 a17791ef… |
| 独立 IR-S1 | 原 probe 9,573 bytes、SHA 7f73dae49a4bed54f090d18e44d137937c93b8dd7b6fa1de9165cd94685e3404，原字节复制并仅执行一次；leaf 入快照、返回后无 live 后代、补杀 0 |
| 独立 IR-S2 | 真正打开 pidfd，分别提供伪 SID、变化的 start_ticks；两分支均拒绝信号，独立 session 在调用后存活，测试最后只清理自己的 fixture |
| 独立 IR-S3 | 本次诊断进程分别暂时移除 pidfd_open、pidfd_send_signal 能力；两分支均 session-unverified，控制进程存活，能力随后恢复 |
| 精确 clean worktree 静态/契约 | Ruff、focused Ruff、mypy 32 文件、format、strict、release check、core export 七阶段均 exit 0 |
| 精确 clean worktree full | 102/102，exit 0；timing 389,541ms；实际进程 389.665338884s |
| full 源身份 | UTC 16:19:07.115768–16:25:36.781098；1082 个运行源输入前后 JSON 完全一致、tracked clean；head/tree 均为冻结值 |
| lifecycle verify | 既有 strict、format、change-governance 实际通过；生成报告保持其原时间与字段 |

**原 probe 的 exit 1 没有被改写成 exit 0。** 它的旧 oracle 期望确认缺陷，修复后原脚本实际输出 `not-confirmed`、退出 1。独立执行前已预注册修复验收条件，由外层 reviewer harness 核实 leaf、snapshot、timeout 和补杀情况后得到 exit 0。二者是不同的判定，原脚本、输出和退出码全部保留于 `independent/`。

独立探针实际发生于 2026-11-17T16:20:30Z，helper 前后字节不变。本人没有重跑 module、ADC、full 或 hosted CI；完整回归证据由 coordinator 在精确 clean worktree 执行后提供，本人独立核对其原始结果和绑定。

## 包装与绑定审查

2026-11-17T16:27:34Z 的独立包装审计核对四组共 84 份可逆 JSON：wrapper hash、还原长度、raw SHA 均一致。50 份直接与各 source_directory 原文件逐字节相等，另直接对照四份关键历史原件；两个 RED、原 hosted 失败和独立 probe 原 oracle 的 exit 1 没有被覆盖。随后另存的两份包装审计原件也已逐字节复核，合计 86 份 raw 包装。

冻结时十个产品文件和 102 个 change 输入的 SHA/长度均与实际文件一致；tracked_overlay 为空。完整原 patch 与实际 base→head diff 一致。正式 canonical 只将稳定产品/政策/validator 用 repository 引用；change 内材料使用 record 引用，普通 archive 移动不需重写这些字节。

`review-input-state.json` 和包装中的 origin/source_directory 是当时的历史位置，不能将它们改成后来 archive 的新路径或重写为新的生命周期状态。checklist、tasks、state、history、后续 review/archive 生成报告有正常生命周期变化；本记录不把这些可变文件作为未来必须保持字节不变的当前源引用。其冻结时状态已由历史 input-state 留存。

证据后包装与 review/archive 不曾进入此前 clean full，属于另行审查的材料增量。后续远端 CI、受保护合并、不可变 Release、Root source-only 晋级需各自精确 source 回执，不由本记录提前证明。

## 适用限制

- 这是独立 AI 源码审查，未执行人类审查、付费模型、native runtime 安装、设备或 provider campaign。
- 本地 Ninja 反例使用 1.11.1.git.kitware.jobserver-1；不冒充 hosted 的实际 Ninja 二进制。历史 CI 镜像清单也不等于每次工具二进制 attestation。
- 未模拟真实 PID 重用，也未对任意 setsid 逃逸给出保证；身份漂移和缺能力分支的范围已分别标明。
- 50ms/256/16 与 1s 的限制仍会使繁忙或缺权限环境得到 unverified/incomplete；不能把这类有限观测解释为全树成功清理。
- 旧主线两轮 15 秒超时原因仍 UNKNOWN；旧 run 不执行 attempt 3。本次通过不证明历史根因、总体稳定性、性能加速、模型效果或 Token/成本收益。
- format 中既有非可执行脚本 warnings 保留；release check 的 runtime_eval_executed=false 保留。远端与实际发行资格以未来真实回执为准。
