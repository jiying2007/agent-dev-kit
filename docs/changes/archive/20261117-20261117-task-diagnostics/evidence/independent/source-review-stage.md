# ADK 11.4.0 独立源码审查：阶段证据

记录时间：2026-11-17T14:58:22Z。审查者：`ai/independent-review`，实际执行代理 `/root/independent_review`；未参与本轮产品实现、实施者测试编辑或版本修改。

## 绑定来源与当前裁决边界

- Base：`5f113b8f5ae6f83662d41d99d0907026f4e44c9d`。
- Head：`d0d2b2dc7cac3e7e7bb853bc372d4afc9975f6bd`。
- Tree：`a643aed639bc871ad3b30f7d9dec14d55dbd8ed0`。
- 完整累计 `original.patch`：89,608 bytes；SHA-256 `7dfafbe77bebdc4628b5833a7dd2944ce3f5b8ec17ba0a184f4551a507460913`。独立重新生成 Git diff 后与保留文件逐字节相等。
- 累计范围：36 个文件，996 insertions / 31 deletions；包括 C2、C1、11.4.0 版本和两份 change contract。

截至该时点未发现未解决的源码 blocker/major。源码与固定验收的对应关系已审；独立定向探针通过。**完整候选回归与最终证据包装尚待协调者完成，因此本文件不是 canonical Spec/Quality pass，也不表示发布、Root 晋级、宿主或 native 资格。**

已阅读本仓库 AGENTS.md、agent-operating-rules、review-policy、review-authorization，两个 change 的 requirements/design/tasks/proposal/checklist/negative-results/state，以及全部产品、测试、文档和版本差异。两份 change 的 checklist 未预先完成，stage 保持 applied。

## C2：历史 attestation 重放

原独立反例在同一次完整 canonical history 中使用 A（readonly）→B（implementation）→旧 A，但给第三次事件分配新 event_id。旧实现仅与当前 attestation 比较，接纳已消费 A。原默认无 verifier 路径仍保守禁止 implementation；测试中的合成 verifier 不能证明任何真实宿主权限绕过。

候选仅在 reducer 本次归约内维护 consumed_intakes。`goal.started` 的有效 intake 和 `goal.updated` 的有效 replan 均加入集合；exact event_id 重放检查仍先于 attestation 消费检查。未携带 intake 的 legacy 事件不消费 None，摘要原有 goal_id 绑定不变。新有效 C、跨 Goal 的合法独立 intake 和保守 trust floor 保持。

独立冻结文件未改：

| 文件 | SHA-256 |
|---|---|
| frozen-inputs.json | 1bddace1b0edebc3475f8e51f1cd0d9a4878c5e9f0c4b17d6d2bf001a2779d60 |
| replay_frozen_probe.py | b6f5a02415a3310e12fc554f8d166767bf585709b1469c5bd1ecbe10f8ebfa7d |

本轮原样重跑 exit 0，四个控制均满足：旧 A 两条路径拒绝、最新 implementation 在无 verifier 时仍不得 final、全新 C 在既有合成 verifier 控制下可完成。原 baseline exit 1 和原始输入、脚本、输出保留在独立 `c2-attestation-replay` 目录，没有用实施者重写的输入替代。

新增 execution-policy 测试覆盖 exact event 幂等、冲突 payload、新 C、重启后历史消费、不同 Goal、legacy None、错误 Goal/摘要；独立 fresh 25 tests exit 0。target-contract 的 verifier False、异常、1、字符串和 mapping 拒绝是现有生产语义的新增直接控制，生产 verifier 路径没有为这组测试而改写；fresh 脚本 9 tests 与总脚本 PASS，exit 0。

## C1：显式事实诊断

`eval import-task --diagnostics` 只在显式请求时附加外层报告字段；默认参数 False，task_trials 默认路径不变。`diagnose_trace_summary` 先调用原 Trace validator，再深复制事实与带原路径的 findings。Importer 使用已核验 ledger 的 attempts、model IDs、tool outcomes，复用 trace/events 引用，不新增读取、认证入口或资格字段。工具次数、尝试数、wall time 不产生浪费、盲重试、并行等待或节省标签。UNKNOWN 与实际零仍有区别。

独立直接加载 base commit 原始 `task_evidence.py`（SHA-256 `db7ccb927e7741fba8455f23bfb6c5df3bb42665771087e89a2bb2bc002501f2`），在相同已知 fixture 和依赖下比较默认报告。五组输入为普通成功、缺失 model coverage、未执行 acceptance、失败后成功 guardrail，以及既有最大 4,096 events。结果均满足旧默认报告 = 候选默认报告 = 候选去掉 diagnostics 后报告；finding 指针逐个指向原 Trace 的同一事实；修改诊断深复制不能更改原 Trace。

最大事件组包含 4,092 次实际 tool-call，逐 outcome 计数与独立 Counter 相符；没有超出既有输入上限。另将 tool outcome 分别设置为 queued/staged/deferred，base、candidate 默认和 candidate diagnostics 三条路径均以 `task evidence: invalid tool outcome` 拒绝。该控制只证明确定性输入拒绝，不证明外部 delivery 或 exactly-once/no-replay。

Fresh Trace 18 tests、task-evidence 37 tests 均 exit 0。测试包含 alias/no-follow/污染输入边界、失败后成功保留、UNKNOWN 与零、默认 CLI 语义、无额外 package 读取和不执行输入内容。一次较早的工具输出在上下文交接时丢失，未将其视为通过证据；本目录保留的是随后重新执行并完整观察结束的有界结果。

## 资产与范围

AAR 使用既有 reference/template 按需读取，未新增 Skill、runtime、宿主 adapter、scheduler、Goal 权威、schema、依赖或付费调用。版本同步为兼容新增 CLI 功能的 11.4.0；原有 M5 fixture 仅 planned_release 更新，未改任务输入、期待或评分标准。未将方法静态校验转述为模型效果。

## 尚待完成及限制

1. 待协调者精确 source 的完整 regression、strict、format、Ruff、mypy、export 和 release-check 原始证据及输入漂移核对完成后，独立审核证据包装并形成 canonical record。
2. 局部 consumed_intakes 只处理传入的完整历史；本轮没有实现跨宿主持久执行、进程崩溃恢复或外部副作用 exactly-once。
3. 所有新增探针均是明确合成的确定性证据，未执行模型或真实 host/native 场景，无法据此认证模型效果、Token/成本/耗时改善或权限系统。
4. 本报告由 AI 独立审查者实际生成，不是人类审核或 owner/实施者代签。审查者没有写入被审产品代码、运行完整回归或操作 GitHub。

定向 raw 结果、独立 probe 和 source identity 均在本目录；原 C2 before 文件另处不可变保留。
