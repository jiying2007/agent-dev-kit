# 11.3.7 独立只读终审

**Spec：PASS。Quality：PASS。未发现阻塞性的源码、合同或原始证据完整性问题。**

这是冻结源码和已取得本地证据的终审。精确 PR HEAD 的 CI、合并后的 main CI、不可变 tag/Release 仍待平台实际回执；本报告不把它们判为已完成。审阅者为 `/root/completion_research_review`，未参与实现、修改合同或编辑仓库文件。实际审阅开始、证据读取完成及裁决时间分别保存在 `final-review.json`，不沿用早期预审时间。

## 1. 精确审阅对象

| 身份 | 已核值 |
|---|---|
| baseline | `e13bd4788d5638c1eb34c169870f19dfd5285b6b` |
| 冻结 source commit | `e90ffe27be645c343ee73762b709238e2e13713a` |
| 冻结 tree | `3675a3993acc981d0181ece7fba302d50aff15e5` |
| 产品 source version | `11.3.7` |
| 完整差异 | 38 个文件；逐文件 Git 内容、工作区字节与 source-identity SHA256 相同 |
| typed review 使用的零上下文 patch | `d7613eedc2a4c0197311ab0ee5bb5b7766e1f8df457f626febf8cc78381f09f6`，650257 字节 |
| source-identity 中的默认上下文 patch | `626cd1f500c40494edcb0c4219ba917da147753c869ff4d7f3e3f820a9757d22`，661446 字节 |

两份 patch 均独立重新生成并逐字节比较。随后分别使用临时 index 和独立 object store，从 baseline 应用完整 patch，均重建为上述冻结 tree；没有写入仓库 index 或 object store。零上下文 patch 使用 `--unidiff-zero`，未遗漏文件或修改，也未更改检查规则。

全部实现与测试改动已经分区独立深审，本次重新核对其冻结身份并审查完整 38 文件差异及新增文档、版本、证据容器。根 manifest 仅改 version；pyproject、包版本、version-lock、README、CONTEXT 和 software-M5 campaign identity 均同步 11.3.7。A/B 预注册只有 candidate.planned_release 从 v11.3.6 变为 v11.3.7，baseline、任务、训练/holdout、results 与未测量状态未动。

## 2. 实现判断

| 范围 | 审查判断及依据 |
|---|---|
| 并行工作包 | 实际两个目标导出均能取得默认包内资源；源码模板仅在已核根目录且文件存在时可选。范围、权限、owner、停止条件、验证和报告字段仍完整。 |
| Review 快照 | 反馈参考去重到已验证的 canonical snapshot；实际 mtime-only Git 反例和独立复跑证明新路径不刷新 index。分支、staged/working-tree 与机械/语义判断边界保留。 |
| 获取、成长、归档 | 父入口保留 pass/partial/not-verified/needs-fix 和局部内容；成长 metadata/README 与授权范围、index-first 一致；未知 hash 差异先保留旧值和内容，不能只重算消除异常。后两类证据明确为静态合同及限定任务观察，没有虚构现场事故。 |
| CMake / SIL-HIL | 真实 all-skipped exit 0 缺口得到针对性修正。CMake 只执行一次 CTest，使用唯一新报告目录，保留非零退出；parser 拒绝缺失/畸形/未知状态及失败，混合结果明确 partial，必跑身份仍须核对。compile-only 不求值测试 preset、不执行 Python/CTest；HIL 示例只收集报告，资格判断另行说明。 |
| 命令超时 | 默认工作预算仍为 15 秒，无自动重试；保留两流、执行标签、work/cleanup 耗时，只终止本次拥有的进程组，并限时排空/回收。独立短预算测试验证两流、本组终止、无关组存活；额外脱组持管道探针有界返回并明确 pipe-drain-incomplete。没有声称解决旧 CI 超时根因。 |

CTest 3.21 的 JUnit 状态格式已有固定版本原作者源码依据，当前实际运行版本为 3.31.6。新的真实 Make/CTest 场景用于结果语义，不冒充 Ninja Multi-Config 验证。最少一个 actual pass 只解除“完全没有通过测试”的失败条件；混合结果和必跑集的任务资格没有因此自动获批。

## 3. 原始证据和全量清单

独立解码并比对五个 durable container 的 **131 个记录**：consumer 20、embedded 59、general 23、integration 13、research 16。容器内容、记录字节数和 SHA256、retained-files-index、当时原文件均一致，保留原始末尾换行、空 stderr、失败日志和 patch；没有为格式检查改写原件。索引和容器一一对应，无重复或缺项。

又核对新增最终验证容器的 **7 个记录**：source identity、运行 receipt、timing、stdout、stderr、性能预算和默认上下文 patch；均与实际原件逐字节一致。131 与 7 是不同阶段的保留集，不把最终数据倒填进早期冻结证据。第三方全文不在上述交付中；来源索引中的 scratch locator 明确是研究时读取记录，固定 URL/commit/blob/hash 用于复核。

portfolio 与 manifest 精确对齐 **65 个入口、53 个资源、118 个唯一路径**。逐路径核对 baseline 和冻结候选的 Git 字节数与 SHA256，7 changed / 58 retained 与实际差异一致。两位审计者的逐项判断均有依据；本审阅独立验证全清单身份、闭合性和全部变更，没有冒称自己又语义深读了一遍全部 58 个保留项，也不把保留视为现场认证。

8 个 profile 的 entry/support 文件数值由固定 Git blob 独立重算，与 measurement 一致；`profile_context_ratchets.json` baseline/current 原字节相同，SHA256 为 `f283524ecff14179cad628735bef9e20580da00c2505687ecca9530da3737bff`。entry 和总字节均未超原 cap，未改 CI、性能或发布门槛。这些是源文件字节，不是实际 Token、成本或模型效果。

## 4. 已完成验证及严格边界

- 完整回归真实 receipt：2026-11-16 02:56:13.765311 至 03:01:14.341414 UTC，退出码 0，**102/102 测试组通过**。外层 300.576 秒；timing 内部 300419 毫秒，现有 600000 毫秒预算检查通过。stdout、stderr、timing 摘要与 receipt 对齐；38 个源码文件执行前后不变。
- 定向命令示例记录：37 个方法中 **32 实过、5 本地缺 Ninja skip**。已检查全部五条真实 skip 日志；GitHub Actions 缺工具 hard-fail 仍在。组级 PASS 不能替代这五项执行。
- 本审阅者此前独立执行两个真实导出/Git 方法和 11 个 runner/CTest 方法，均实过、无 skip；所绑定源码 SHA 与冻结版本相同。默认 15 秒 GREEN 与原 15 秒 RED 已有真实原始回执，本次没有为了增加通过次数重跑。
- 首轮工具 PATH 含空格导致 GNU make 夹具失败、遗漏 PYTHONPATH 的 import errors、all-disabled false-pass 假设被 exit 8 反驳，均原样保留并准确分类。没有把环境错误写成 Skill RED。
- 四项消费产物独立判为符合给定任务；14 个输入再次核对未变。它们是**一个新上下文会话中的四个单次定性任务**，没有旧版/无 Skill 对照、重复独立样本或原生宿主测量，不能宣称 A/B 提升、任务成功率、真实邮箱操作或真实下游 worker 执行。

## 5. 研究和打包判断

独立 8 仓库/12 入口的原始来源索引完整保留；新增 OpenAI、Anthropic 两个官方 skill-creator 入口及局部 Apache-2.0 许可证身份另列。四个官方 Skill/license 的固定 commit、blob、SHA256、字节数与原始读取一致。研究合计 10 个源仓库/14 个入口，范围有限且明确，不声称穷尽全网或审完每个上游仓库。

采用理由对应实际缺口；已有精简入口、渐进读取、真实任务及对照评估方法保留。DMA 示例所有权冲突、tick/毫秒混淆及特定 SPI 默认值被写为有来源的静态拒绝理由，没有虚构硬件复现。无许可证来源只比较方法，没有复制资产；未执行外部模型 API/CLI 优化器，也未继承上游的新权限/审批流。

额外检查了 root 添加的三个证据包装文件：verification.md、evidence/original.patch、evidence/final-validation/raw-evidence.json。叙述区分发现阶段与后续观察、两种 patch 身份、组级结果与五项 skip、单次消费与未运行 A/B。三者是冻结源码后的证据包装，不属于本次 38 文件源码目标；未改变这 38 个文件。

## 6. 裁决与待办

**冻结源码 Spec PASS / Quality PASS；零 blocking findings。** 可以进入已有授权的正常 PR 和精确源码平台验证流程。合并/发布资格仍须由后续精确 HEAD CI、main CI、tag/Release 与资产摘要的真实对象完成，不能由本报告替代。

审查机械探针首轮自身出现两个分类错误：把 JSON 中嵌入的 patch 文本计入顶层 diff header，以及把已说明的三项 staged 证据包装判为源码漂移。已保留首轮结果与脚本，改为行首 header 计数和“原 38 个文件不变、仅允许三项已审包装”的边界后通过；这不是产品失败，也没有修改产品以迎合检查。最终复核见 `identity-check.json` 与 `scope-check.json`。
