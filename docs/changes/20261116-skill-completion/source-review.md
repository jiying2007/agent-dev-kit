# 外部方法检索与采用

检索日期：2026-11-16。承接历轮研究，本轮重新检索官方规范、官方 Skill 作者和嵌入式/测试/数据获取维护者。独立研究读取 8 个原作者仓库的 12 个 Skill 入口、4 个参考文件；root 补读 OpenAI、Anthropic 两个官方 skill-creator 的有关方法章节及各自 Skill 内许可证。合计 10 个 Skill 源仓库、14 个具体入口；不声称穷尽互联网或审完这些仓库所有资产。

## 方法选择

| 方法 | 本轮差距与处理 |
|---|---|
| 随包资源自足、按需加载 | 实际两目标导出缺根目录模板，默认改用已有包内工作包；不增加模板镜像或源码依赖。符合 Agent Skills specification 与 Microsoft Agent Framework 的资源加载边界。 |
| 单一可执行方法来源 | 真实 Git 反例发现 feedback reference 残留旧快照命令；去重到已经验证的 canonical reference，消除两个副本的行为漂移。 |
| 按真实产物判定结果 | CMake 的全部动态 skip 可返回 0；改用同次新 JUnit 的真实状态，保留部分结果、必跑集和后端边界。官方 v3.21.0 writer 与当前实测共同限定解析规则。 |
| 可诊断的有界执行 | Python 官方语义与真实 15 秒反例分别证明可捕获输出和后代残留；补日志、执行身份和自有进程组回收，不放宽预算、不虚构上次超时根因。 |
| 具体任务、原始产物、客观验收 | 官方 skill-creator 的真实任务迭代及质量/时间分开观察与既有 ADK 方法一致；本轮沿用确定性反例和最小上下文对话试用，不引入官方例子中的外部 CLI 调用或未经授权模型费用。 |
| 精简入口、避免重复常识 | OpenAI skill-creator 的简洁/渐进式方法用于检查现有去重方案；没有重写所有正确 Skill 或凭源码字节推断 Token 效果。 |

## 明确保留或拒绝

独立研究报告与固定身份索引见 `evidence/research/`。Mindrally 的 DMA 示例在消费前重启同一缓冲；rovinax 的 `osDelay(1)` 混淆 tick 与毫秒；lhbsaa 的 SPI 4092B 是特定配置默认值而非通用硬上限；这些是有原始依据的静态问题，没有声称上板复现。ADK 已有目标/版本/所有权方法保留。testing-skill 的绝对删测试规则、IMAP wrapper 的 Seen/凭据风险、新运行时或隐式安装不纳入。

brunofbloq 的 QA/精确目标方法仅作比较，其检索时无可见 LICENSE，不复制原文资产。arjunprabhulal 的 divergence point、caller-first 与边界数据多数已覆盖，其未完成的无 Skill 基线评估不能作为效果证明。theory-vs-result 的确定性缺陷/统计效果区分已有覆盖，不引入额外审批层。

## 官方补充身份

| 来源 | 固定 commit / Skill blob | 决定 |
|---|---|---|
| anthropics/skills 的 skills/skill-creator/SKILL.md | `1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064` / `65b3a402dbd09b8e83f9d637c6b553875189085c` | 具体任务与产物检查已覆盖；不运行外部模型/CLI 优化器，不把单次试用写成 A/B 提升。 |
| openai/skills 的 skills/.system/skill-creator/SKILL.md | `49f948faa9258a0c61caceaf225e179651397431` / `72bc0b97e7a6476254a9d5c424c9971748402ec3` | 简洁、条件性 references、自包含资源；按现有问题落地，不改 ADK 已有 Manifest 格式。 |

两个官方 Skill 的局部 `LICENSE.txt` 均为 Apache-2.0；根目录 `LICENSE` 探测返回 404 后改查实际局部许可证，不以仓库 metadata license=null 推断无许可证。固定 URL、原文 SHA256 与 blob 校验在官方补充索引中。

第三方全文只留研究输入，不进入运行时包或本轮 Git 交付；提交的方法摘要、固定源身份和可重新获取的 URL 足以追溯。研究索引中的原始 scratch locator 是历史读取记录，不声称该全文已随仓归档。全部研究只是采用依据，实际源码、测试、审查和发布各自验收。
