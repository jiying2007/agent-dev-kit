# v11.3.11 独立 Spec / Quality 审查

**Spec PASS / Quality PASS。未关闭 blocker、major、minor 均为 0。**

实际 reviewer：`ai/root/delivery_review`（独立只读 AI）；完成时间：`2026-11-16T12:40:08.744429+00:00`。最终裁决晚于完整回归完成时间 `2026-11-16T12:37:28.154870+00:00`。

## 可见更正：SER-REVIEW-01

冻结的 `negative-results.md` 最后一条曾把不支持 `--profile` 的命令写为 exit 2。**实际原始 `unchanged-context-budget.json` 明确记录 `returncode: 1`；以原回执为准。** 这是 minor 证据文字错误，本报告以可见追加更正闭环。旧句保留为冻结历史，不改失败回执、不改测试或门禁、不因此重复102套件；后续 verification 包装必须保留此更正。它不是产品行为失败。

## 源码与身份

- 基线：`b20df018ca62436dd026daed6ec6944d4a45cbbd`。
- 本地受测提交：`5b253b8885447f35f015d63950db025b2d82b2ba`。
- GitHub connector 正式源提交：`a94ae0d551a8ede9f8387e4cd03eb41daf1894b1`。
- 二者共同 tree：`35fa327dff1c4339c5637a427be64ca6c810f705`；父提交都为基线。
- 完整 canonical patch SHA256：`446fcc6a3a599051177bfd00a5fd5590b3d270fbad41554d5dfc9752eba605e7`。
- 实际检查28个变更路径的大小、SHA256与Git blob；本地与正式源完整tree相同。

提交元数据不同，因此没有声称本地 full 在远端 SHA 上执行。后续受保护 PR/main CI 仍须绑定实际远端 SHA。full与独立probe前后工作树clean；审查末集成者已切到同tree的正式源并追加尚未审查的包装文件，不能把当前整个工作树写成clean。28份冻结源身份仍逐项一致，reviewer没有修改源码、index或refs。

## 规格判断

现有 optional 供应链 Skill 只在凭证对象/整对象输出场景加载已有 reference，原 source-only、adoption、runtime 范围保持。新方法能沿字段来源、holder、serializer、sink检查当前diff外的另一端；明确关键词零命中不能证明安全，未证可达性保留unverified，不执行不可信候选。Python3.12官方field/asdict文档与本轮独立回读的Sentry固定源均支持repr只覆盖repr、asdict递归包含字段的区分。

显式字段投影被限定于输出合同与已知非敏感值，避免将endpoint或任意字符串默认认作安全。示例只用合成值，坏输出只留内存，stdout为布尔结果；不修改输入对象。没有引入新Skill、路由、扫描引擎、依赖或统一门禁。

这是审查方法缺口补齐，不是发现或修复ADK生产凭证泄露的证明。

## 实际验证与测试区分力

- 独立执行最终reference提取出的3项测试，全部通过，包含普通/`-O`/`-OO`示例、动态公共字段/嵌套值/输入不变，以及Claude Code与OpenCode显式optional导出。
- 仅在scratch构造6类坏实现：重新加入敏感字段、丢必要endpoint、硬编码公共值、改输入掩盖泄漏、移除repr保护、回显原整对象。**6/6被现有测试拒绝**；原实现仍通过。此检查补强原RED主要来自缺示例/导航的区分力，不把测试失败次数当模型成功率。
- 完整回归由集成者实际执行，原始receipt/timing/logs已独立核对：**102/102，exit0，无超时，342.106898秒**。before/after均为本地受测commit/tree且clean；102个唯一注册项全部pass，日志含新方法各项通过。stderr含正常unittest输出，不能误称为空或失败。
- 8个profile原始stdout/result逐项一致且全部pass；阈值文件与基线完全相同。large-refactor为323321/323328 bytes；主Skill入口仍140行。
- 全部Skill资产仍153文件，源码422513→425477 bytes，净+2964。此处仅是UTF8源码量，不是Token、初始上下文、费用或时延测量。

## 消费者观察

独立阅读消费者报告及fixture全部三文件、最新diff后确认：报告正确追踪新credential经既有Envelope/asdict/JSON进入failure_event返回值，且分别排除repr和显式attempt公开输出的误报。真实logger落盘、ACL及生产泄露保持unverified。缺许可证是候选引入的缺证，符合原供应链范围；没有执行或导入候选、安装依赖或读取真实凭证。

该单次任务只能说明此具体消费任务能够使用新方法，不能作为成对基线、重复模型A/B、盲评或效率提升证据。

## 阅读范围与证据

全文读了适用规则、受影响Skill/reference、新测试、需求/设计/任务/审计/负结果、实现probe/recorder及主要原始回执；完整检查所有生产与版本投影changed hunks。65入口全文重读是portfolio reviewer的记录，本reviewer核对其范围、结论与153资产摘要/集合，未冒称重新语义通读65入口及全部bundled资源。完整阅读消费者报告与三份fixture，回归核查为真实回执/日志摘要/新增测试记录，不重复执行完整套件。

Sentry固定commit为a582c51ee29d0f35e6ac321340796f77d43da733，两份方法文件完整回读，许可头12行核对Apache2.0；Python3.12官方文档针对field repr与asdict递归段。没有整体复制上游正文。

28份冻结源及16份主要证据的完整大小/SHA256、外部链接、实际阅读范围和限制见同名JSON。独立探针报告SHA256为`a60f8ac8f3ed68789485ecc72ef9cd1469732317e07f1a1cb59ac1285f48efd2`。

## 边界

本报告只批准精确冻结源码范围及已有验证证据，不预先批准后续包装、typed记录、PR/main CI、不可变发布或Root接入。没有真实模型效果、provider用量/费用、运行态discovery/load/trigger、板端/HIL、现场或M5新资格；不继承测试名称所暗示的实际认证。后续交付阶段仍按原流程取得各自真实回执。

首次生成本报告时，原28路径、同树映射及full回执均已通过，但“整个worktree必须clean”断言因集成者同期追加4个untracked包装文件而退出1；该真实工具输出与原因保留在机器报告中。当前改为如实记录包装中的worktree状态，冻结源身份继续严格核验；没有将此review harness断言失败记成产品失败，也没有重跑或改动产品测试。

机器报告SHA256：`901ba57d1a79dbe3514ed41ccf4551214af3bfd602e4c97515ef0a4f9ccf4909`。
