# 验证与交付记录

## 原始记录的可见纠正

冻结源码的 `negative-results.md` 将不支持 `--profile` 的命令退出码写成了 2；实际 `evidence/implementation/unchanged-context-budget.json` 中的 `returncode` 是 **1**。原始错误回执保留，以实际 exit 1 为准。这是文档笔误，不是被修改过的测试结果，独立审核记录保留该 minor 发现。

一次向 connector 准备源码树的本地 JSON 输出超过工具输出上限，解析失败。后续分块读取完成；GitHub 返回的 tree 与原本地 tree 精确相同。该失败没有改动源码、门禁或远端分支。

## 源码身份与完整验证

基线为 v11.3.10 / `b20df018ca62436dd026daed6ec6944d4a45cbbd`。本轮本地冻结并实际运行测试的提交为 `5b253b8885447f35f015d63950db025b2d82b2ba`；GitHub connector 创建的正式源提交为 `a94ae0d551a8ede9f8387e4cd03eb41daf1894b1`。两者 commit 元数据不同，**tree 均为 `35fa327dff1c4339c5637a427be64ca6c810f705`**，28 个变更路径 bytes/Git blob/SHA256 一致；没有将本地运行伪写为远端 SHA 执行。

完整 canonical patch SHA256：`446fcc6a3a599051177bfd00a5fd5590b3d270fbad41554d5dfc9752eba605e7`。源绑定、补充消费者原材料与实际执行日志见 `evidence/source-bindings.json`、`execution-summary.json`、`execution-bundle.json`。bundle 对原始文件使用无损 gzip+base64，每份保留原始大小与 SHA256；原 stdout/stderr 和失败观察均可恢复。

| 项目 | 实际结果 |
|---|---|
| 全体入口增量审读 | 65/65，另定向全文读取14份reference；153份资产仅做机械清单，未冒充全文阅读 |
| 新方法测试 | 3/3，通过普通、`-O`、`-OO`执行、嵌套/Unicode/空值控制、输入不修改及两个目标optional导出 |
| 独立错误变体检查 | 6类坏实现均被已有测试拒绝；具体变体、命令及结果保留在独立探针 |
| 完整本地回归 | **102/102 注册测试入口，exit 0，无超时** |
| 运行时间 | 北京时间2026-11-16 20:31:46至20:37:28，342.106898秒 |
| 源码前后身份 | HEAD、indexed tree、working/index status完全相同，均clean |
| 原8个Profile预算 | **8/8通过，阈值文件未变** |
| Skill资产规模 | 153文件，422513→425477 bytes，净+2964；只增强一个optional Skill |

`large-refactor` 仍为323321/323328 bytes，`embedded-fullstack` 仍为316439/316854 bytes。8个Profile不默认包含本次optional Skill，数值与基线相同；主入口保持140行，按需参考64行。以上是源资产字节观察，不是Token、成本或时延测量。

## 独立消费者观察

消费者收到原始3文件adapter fixture和审查任务，调用配置为 `fork_turns=none`，没有收到预期答案。其报告实际找到了新增字段经未修改文件 `asdict`→JSON 的通路，并分别排除了repr与显式公开字段路径的对应误报；未执行候选代码或读取凭证。报告额外指出该候选缺少许可证证据，符合原供应链范围。

这是单次新上下文源码审查观察；完整执行transcript未留存，不能作为成对模型A/B、胜率、因果效率或native认证。补齐的是Skill方法缺口，不代表发现了ADK生产凭证泄露事故。

## 源审查、发布与消费端

最终独立Spec/Quality裁决由 `evidence/independent-source-review.json` 提供；typed record绑定源码、原始patch、政策与validator。后续包装仅追加证据及本纠正记录，不修改已冻结28个源路径。受保护PR、精确main CI、正式不可变Release与Root source-only接入使用各自真实回执，不能由本地通过预先代替。

v11.3.10 已合并且精确主线CI 43866309947成功。其发布run 43867568341第一轮package job 133300078878实际为60/61：ADC示例在configure完成并进入构建后超出原15秒预算，完整日志已保留。一次有界复验job 133303201333再次在相同测试超时，发布步骤均skipped，未生成正式Release。本地两次原始单测分别用0.292秒与0.279秒通过，但工具链版本不同，不能由此推断CI故障原因。Ninja的`[1/4]`是完成的构建边数，不能定位为第一条编译命令卡死。根因尚未确诊；未增加预算、跳过用例或追加发布重试。

交付使用已授权的GitHub connector分支、commit/tree、PR、merge与Actions失败job复验；权限限本任务两个仓库的现有范围，不改变保护规则或授予新的工具权限。网络/写入结果未知时先读回核对。当前缺少 `~/codex` 的Knowledge Provider/Execution Policy，沿用既有source-only授权，未更新live资产、运行态资格或M5状态；没有启动外部Codex/Work或付费模型任务。
