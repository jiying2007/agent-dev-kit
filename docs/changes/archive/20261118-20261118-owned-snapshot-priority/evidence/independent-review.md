# 独立最终审查：20261118-owned-snapshot-priority

## 裁决与身份

**Spec：PASS。Quality：PASS。** 没有未解决的 blocker/major；OSP-1、OSP-2 均由实现者修复，并由本 reviewer 使用冻结的核心反例独立复验。该裁决只适用于下述精确源码及明确保留的本地验证和包装证据，不提前认证后续 PR/main、Release、Root 或运行态资格。

Reviewer 为 `ai/independent-review`；helper 实现作者为 `ai/implement-snapshot-priority`。Coordinator 负责需求/设计、九项版本投影和证据编排。本 reviewer 只读被审产品，独立产生反例、报告与 canonical；没有代写修复或修改验收。实际审查时间、证据完成时间、政策和 validator 摘要见同 change 的 `review-evidence.json`。

| 来源 | 精确身份 |
|---|---|
| base | `021d81aa4923dbc68a934d9cd0d64c4dfed76167` |
| tested product head | `64d120ebcbc5d77fd90af99bac2bb9f4f3a13682` |
| tested product tree | `35a666c2b4349b1890f5788241ac32bcf8080e38` |
| helper SHA256 | `2be3cbba83ee965bdba635fc5e5d30263e6ecce7f694a1e9c75833b8a39be295` |
| complete original patch SHA256 | `2c13a35d33d1c56872efa32b0f337e7fbbfbb9f6804eb146f8c646b990c7d605` |
| frozen input state SHA256 | `6066a4c2ebfbbf0fde109048638bc5a81a84fcf4e24b0f7d212305d4252c9f4c` |

完整 39,716-byte 原 patch 与实际 `git diff --binary BASE HEAD` 字节一致。十个产品文件逐个核对了 Git blob、当前文件和冻结摘要；tracked overlay 为空。其余九项只有 11.4.2 版本/变更日志投影，预注册仅改 planned_release，未改 holdout/task/grader。原 ADC/CMake、CI/gate、测试顺序和预算文件均未修改。

## 验收判断

| 验收 | 判断与证据 |
|---|---|
| ACC-001：无关前缀后的自有发现 | 各线程 children 只作优先线索；缺接口时在同一 cleanup 截止内续扫 global cursor。固定前缀 RED 保留，最终真实 Ninja 的 256-prefix、非主线程后代与 foreign session 独立控制通过。 |
| ACC-002：预算、截断与完整性 | 每批 50ms/256 entries、累计 16 records、总 cleanup 1s 保持。4096/MAX+1 children 边界、半 token 拒绝、cursor 关闭、fresh pass 和无进展停止有静态与定向证据。OSP-1 的计数边界和 OSP-2 的累计截断资格已独立修复复验。 |
| ACC-003：真实清理与身份安全 | 原真实 Ninja 方法及三个身份函数与 base 逐字一致。信号继续经 pidfd 打开后 PID/SID/starttime 核对；发现链不授权。真实探针返回后 launcher/leaf 不存在，foreign session 仍活，fixture 没有补杀。 |
| ACC-004：兼容、负结果和完整回归 | 最终模块 66/66、0skip；八阶段全部 exit 0，完整 102/102。旧 RED、能力缺失、fixture/PATH 问题、两次被停止的 full、治理格式失败均保留。 |

旧 global scanner 的前缀饥饿属于已确认的源码边界；修复没有把本地缺失 children 的事实推广为 hosted 原因，也没有把任意主动另建 SID 的逃逸纳入本轮保证。

## Findings

### OSP-1 — major / fixed

原候选在 global 第 256 项为 numeric PID 时先 advance cursor，再因二次取额度拒绝 stat，导致 fresh pass 同样漏读。原独立输入为 255 个无关项和 PID 9000；实际缺陷记录保持原件。最终把 global entry/stat 作为同一已预留单元，不扩大预算。更新来源绑定后的相同核心输入在两个 fresh pass 均读到 PID 9000，两个 cursor 均关闭。

### OSP-2 — major / fixed

原候选可在各批均 observed 时因累计 17 PID 截断为 bounded，却返回 complete。此反例只证明 ACC-002 的资格矛盾，不证明活进程漏杀。最终 verified 同时纳入累计 report.status 及 records/batch_results 两种截断。原三 pass 输入最终为 session-unverified，所有 17 个 fresh 合法记录仍进入模拟清理；独立 17-batch 控制也保守降级。

两份原 collector 副本仅替换 candidate commit 和 expected helper hash，核心输入和旧缺陷 oracle 均未改；其真实退出码是 **1 / not-confirmed**，并非脚本成功。独立恢复 oracle 依据正向验收条件实际 exit 0。原报告中发现时的 open 状态保持，当前 fixed 由后继原件证明。

## 实际执行证据

最终完整模块由实现者运行于 17:10:51.830617–17:11:01.177017Z，66 tests、0 failure/error/skip；同源 Ruff/diff check 退出 0。本 reviewer 只读核其原件，不冒称是 reviewer 自己执行。

独立组合探针实际运行于 17:13:14.999417–17:13:16.527131Z、exit 0。真实部分只注入根 `/proc` 枚举顺序，保留真实 stat/task/pidfd/信号。Ninja `1.11.1.git.kitware.jobserver-1` 的新 PGID 中，非主线程 TID 39 创建 leaf PID 40；launcher PID 38、leaf PID 40 在 helper 返回后且 fixture 清理前均不存在，foreign PID/SID 34 身份未变并存活，rescue_signal_pids 为空。四批观测、两个 iterator 都关闭，最终 report=bounded、cleanup=session-unverified；这不是性能或 hosted 证明。

完整验证在独立 source/probe 收敛后才运行：clean detached exact head，实际 UTC **17:13:37.985541–17:20:28.694200Z**，进程 410.708667527s，runner timing 410,588ms，**102/102、exit 0**。Ruff、focused Ruff、mypy 32 源、format、strict、release check、core export 七个前置阶段也全部 exit 0。before/after 的 1,082 个 operational 输入逐项完全一致，并与审查时当前 tracked 源一致，HEAD/tree/clean 未漂移。

紧凑 full 日志只输出成功组名称，内容摘要可与另一轮全通过运行相同；本轮身份由实际时间、timing JSON、精确 head/tree、完整原始 argv 和 before/after 清单共同绑定，不把 log hash 当唯一 run ID。release check 中 runtime_eval_executed=false；本轮未据此声明模型或运行态效果。

## 包装完整性与生命周期边界

Reviewer 实际执行 `independent-packaging-audit.py`，于 17:22:51.587334–17:22:51.939321Z 完成、exit 0。核对了冻结输入的 166 项、十个 wrapper index、**145 个可逆 wrapper / 1,636,250 原始 bytes**。除两份有意保留的旧 verify 格式失败快照外，解码原文均与原 scratch 文件逐字一致；两个历史 origin 已被后继正常内容替换，不把 origin 路径冒充当前原文身份。wrapper 的原始大小/SHA 和包装 SHA 均有效。

本 reviewer 的 21 份原件及原 index 未改，单独核对通过。正常 lifecycle verify 实际通过；此前缺既有负结果表格 section 的失败先保留再修格式，没有修改 gate。本次将成功 verify-report 另存为 `independent-verified-lifecycle.json` 历史快照，避免未来 lifecycle 输出影响当前证据。

完整回归测试的是上述产品 tree；后续 change 文档、原件包装、审查报告属于另行审查的证据增量，不能冒称已包含在该次 full tree。Canonical 对 change 内材料使用 record-relative 引用；产品、政策与 validator 使用 repository-relative 引用。不直接绑定将正常变化的 tasks/checklist/state/history/review/archive 输出。review-input-state 是采集时的历史快照，其内部原路径在归档后仍是历史位置，不改原字节伪装成新路径。

## 保留限制

- 11.4.0 两次 ADC/CMake 15s 等待原因、11.4.1 hosted bounded 的具体原因仍为 UNKNOWN；不由本轮通过反推根因已修。
- 两个前候选 full 实际被停止、exit 130；原件保存，未改为 PASS。原定向 RED、名字含 green 但实际失败的首版记录、mock fixture 错误、reviewer 首次 PATH precondition 失败及 verify 格式失败均保留。
- 本地 children ENOENT 不代表 hosted 能力；fake-proc、固定 clock 与模拟 ACK 只支持相应分支判断，不能替代真实信号、压力性能或长期运行证据。
- 未执行付费模型、live runtime 安装、设备、当前 M5 或 Token/费用收益测量；没有人类审查、provider 执行、现场资格或 release 授权声明。
- PR/main required checks、不可变 Release 与 Root source-only 尚待各自实际回执，TASK-003 不能由本记录提前完成。

实际 typed validator 的调用结果在 `validator-result.json` 单独记录；validator 验证记录结构和摘要，不代替以上语义裁决，也不自行产生发布权限。
