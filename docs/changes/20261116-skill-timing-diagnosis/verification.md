# 执行时序与诊断精度：验证与交付证据

## 准确来源

- 基线：v11.3.8 / `913b6b3a0838ccddae252a3a8536ac7d41598810`。
- 最终受审源码：`b4c2a30384542abdd2db1b6ba524f7f3a3b002b9`，tree `475d2fa8ff69320bf5268677eb4072e7359e5ab1`，版本 v11.3.9。
- 完整原始 diff：`evidence/original.patch`，SHA256 `02f31f5fd6f932c5c52892fda46633d0510eb0ec1f66db461f78041a27f2917a`；29 个变更文件逐项绑定见 [source-bindings.json](evidence/source-bindings.json)。证据包在源码冻结后追加，不把证据提交身份与被测源码身份混淆。
- 全量覆盖：34 个通用 core、22 个领域 core、9 个 optional；153 个被 Git 跟踪文件、421,746 字节基线逐项校验 blob/SHA256/长度。4 个 Skill 修改，61 个保留且有逐项理由，见 [audit.md](audit.md)。
- 上游固定索引覆盖 16 个仓库、23 个具体文件（包括许可证；完整/局部阅读范围分别保留）。见 [source-review.md](source-review.md)。这不是穷尽互联网或整个外部仓库的质量认证。

## 方法变化及验收

| Skill | 版本 | 本次变化 | 实际验证 |
|---|---|---|---|
| adk-systematic-debugging | 1.2.5 | 重跑前保存易丢失证据；good/bad/untestable 分类，未知或执行错误终止；保留 bisect 日志和歧义候选 | 5 个测试执行发布引用中的完整 shell 示例；真实临时 Git 历史与 139 个 subprocess 回执；未将不可测修订误判为目标坏提交 |
| adk-rtos-task-design | 2.0.3 | tick 单位/量化/范围；绝对周期与真实截止时间；timer callback 非阻塞和停止后的所有权/静默条件 | 3 个测试编译发布 C 示例，19 个字面量向量、空输出指针与两种错误实现拒绝；实际 FreeRTOS/CMSIS 头文件探针；没有板端调度资格 |
| adk-incident-rca-report | 1.1.1 | 区分事件与采集时间，保留时区及未知时钟偏差；按实际缺口选择后续行动 | 时区/迟到数学设计案例；受限工程消费 B 保留 unresolved，没有从采集顺序推导根因 |
| adk-skill-composition-governance | 1.1.7 | 空白 Creation Gate 由 pass 改为 pending；初始化只展开当前所需章节 | 原模板 10 个无证据 pass 子项实际 RED；修复后结构测试与 optional 安装通过；原消费 C 发现范围缺口，修补后由新线程复验 |

12 个新增测试被并入既有 Skill 内容入口，实际内容测试为 152 项。RCA 数学案例和模板解析测试证明有限确定性性质，不伪称模型行为对照实验。

## 完整回归与容量

最终源码完整回归在 2026-11-16 13:33:36 至 13:38:52（+08:00）执行，耗时 **316.694 秒，102/102 组通过**。运行前后 HEAD/tree 相同且工作树 clean；[原始回执](evidence/full-regression.json)、[计时](evidence/full-regression-timing.json)、[stdout](evidence/full-regression.stdout.log)、[stderr](evidence/full-regression.stderr.log) 均保留实际字节与摘要。

初始 `7e47130...` 源码也曾完成 102/102，但其后发生生命周期范围修补；该次日志单独保留为 `initial-regression*`，不替代最终源码回归。

8 个 Profile 均通过原有 source-growth ratchet，没有增加阈值或修改 checker。`large-refactor` potential source 为 323,191 / 323,328 字节。全部 Skill 源文件由 421,746 增至 422,088 字节，净增 **342 字节**，见 [尺寸比较](evidence/skill-source-size-comparison.json) 和 [原容量结果](evidence/profile-context-checks.json)。这是源码容量核算，不是 Token、加载上下文、延迟或成本测量。

## 独立审查与消费发现

独立只读审查者 `ai/root/independent_round2_review` 对完整 diff、65 项覆盖、上游固定原文/实现、可执行示例、真实回执和原始消费回答进行了 Spec/Quality 双维审查；正式裁决与范围见 [独立报告](evidence/independent-source-review.json)，机械绑定见 [review-evidence.json](review-evidence.json)。审查者没有编写本次实现，也没有进行远端写入。

IR-C1 保留原判定：首次 C 的十项 Gate 均正确 pending，但输出 96 行、12 个标题、3,894 字符，展开大量本次无输入的阶段，未满足最小初始化要求。修补后独立新线程的实际回答为 41 行、5 个标题、2,096 字符，仅保留 Scope、全部 Gate、后续审核入口与来源，独立审查接受该次输出范围。原始请求/回答和复验请求/回答均保留在 `evidence/consumer*`；不得把原结果改写成三案全通过。

第一次线程同时处理 A/B/C，复验线程只处理相同 C；任务为合成的受限工程请求，没有固定采样、原生加载 trace、无 Skill 基线或 held-out 对照。这些观察可支持本次交付检查，不能证明文案的单独因果效果、总体成功率或 Token 收益。A 的 RTOS 判断和 B 的事故短报告被分别复核，仍不代表真实现场事件已解决。

原上游正文的恢复、新检索和独立复取分别记录；没有把新的检索回执追称为旧回执。独立引用路径所对应的持久副本通过 `retained-files.json` 与 `independent-retained-files.json` 映射，固定来源地址与摘要支持重新核对，不整体分发外部 Skill 实现。

## 完成范围、平台交付与回滚

T1–T4 的源方法与验证结果已完成。T5 的实际双维裁决、已关闭发现、策略和校验器摘要由 typed review 记录承载。T6 使用既有受保护 PR/main CI、不可变 Release 和实际下载归档检查；这些后续平台事件按真实发生时间记录在承载本变更的 PR，静态源码不预填尚未发生的发布结果。

不宣称原生 runtime、真实 FreeRTOS 调度/取消协议、HIL、硬实时、付费模型 A/B、Token/成本或产品/现场资格通过。现有资格和 holdout 记录未被新结果替换；prereg 仅调整下一候选身份，历史未测量状态保留。

回滚以独立受保护 PR 恢复本轮四个 Skill 与对应测试/版本投影，重新运行受影响检查；不改写历史日志或发布资产。Root 仅在正式不可变发布被验证后，通过既有 source-only 事务消费准确 Gitlink；不会因此生成宿主或产品资格。
