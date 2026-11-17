# 外部来源与取舍

2026-11-17 检索并只读核验 7 个一手仓库/规范的具体文件，对照 ADK
`6d902f721f560f02883516e809fbd93a326405b6`。这是有界研究，不声称穷尽全网。
源码按下列 commit 经 GitHub 接口回读；网页搜索只用于发现与交叉核实。
未安装外部 Skill、执行其脚本、复制大段源码或调用模型 CLI。

| 来源（固定 revision / path） | 已核方法与 ADK 决定 |
| --- | --- |
| [Agent Skills 客户端指南](https://github.com/agentskills/agentskills/blob/83021e2be457a9b6679148719c1f6074f0ad975e/docs/client-implementation/adding-skills-support.mdx) | **ENHANCE**：Step 5 保护压缩中的 Skill 正文，仅对仍在上下文中的重复激活去重。现有 context/handoff 已记录目标和证据，尚未明确“曾加载”与“当前正文有效”的差别。本次补来源、内容身份、必要引用和恢复取舍；不新增 runtime context manager。 |
| [Anthropic 触发评测](https://github.com/anthropics/skills/blob/e4bb5d960d87126ff3b3a8af1a104b7db67560ba/skills/skill-creator/scripts/run_eval.py) | **RETAIN / 不复制 harness**：重复观测可用；但 `run_eval` 将 worker 异常计作 False，负例可能因此通过。此为静态源码推论，未运行其 CLI。保留 ADK 的 error-free 校验与 runtime-errors gate，不把工具失败计成安全成功。 |
| [Sentry Prompt Optimizer](https://github.com/getsentry/skills/blob/a582c51ee29d0f35e6ac321340796f77d43da733/skills/prompt-optimizer/SKILL.md)及 [优化循环](https://github.com/getsentry/skills/blob/a582c51ee29d0f35e6ac321340796f77d43da733/skills/prompt-optimizer/references/meta-optimization-loop.md) | **RETAIN**：同切片比较、最小改动候选、失败聚类、留出集与停止条件。ADK 已有相关效果/任务评测边界；不重建评测系统，不以措辞变化宣称效果提升。 |
| [Matt Pocock：为 Agent 写作](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/productivity/writing-for-agents/SKILL.md)及 [任务切分](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/engineering/to-tickets/SKILL.md) | **RETAIN / 局部 ENHANCE**：引用同时说明目标与触发条件；按分支下沉细节，同一意义只保留一处。本次 token Skill 将重复字段清单归到原模板；保留条件与字段。现有任务拆分和 expand-contract 方法不重写。 |
| [Superpowers 审查交接](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/requesting-code-review/SKILL.md) | **RETAIN**：固定 base/head、分支 merge-base、只交任务所需上下文。ADK review-evidence-template 已覆盖，并明确 working-tree overlay；不重复添加审查层。 |
| [Addy Osmani 约束方法](https://github.com/addyosmani/agent-skills/blob/39b723ceebf81474d0557c1fecd01eddab585563/skills/constraint-driven-development/SKILL.md)及 [安装边界](https://github.com/addyosmani/agent-skills/blob/39b723ceebf81474d0557c1fecd01eddab585563/README.md) | **RETAIN**：检查按成本分层、基线 ratchet、违规反例检验 checker；ADK 已有。该仓也说明单 Skill 安装缺仓库级共享 references；继续保持 ADK 单项导出可消费，不照搬整包。 |
| [Vercel 分发实现](https://github.com/vercel-labs/agent-skills/blob/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62/scripts/build-discovery-index.mjs) | **OBSERVE**：固定 Git 树、确定性归档、逐 Skill 摘要与独立制品可参考；当前无新增 discovery 服务需求，沿用 ADK 已有导出/发布链。 |

## 许可证与边界

已回读固定 revision 的根 LICENSE：Agent Skills、Sentry 为 Apache-2.0；
Matt、Superpowers、Addy 为 MIT。Anthropic、Vercel 的根 LICENSE 路径返回
404，本轮未确定对应路径的许可证，不复制其代码。只将已核通用方法写入现有
ADK 方法指导；外部来源不扩大授权、不替代独立审核。

## 本轮采用的可验证边界

当前有效正文可去重；正文丢失/被摘要或来源变化须按当前目标和权限按需重读，
必要内容不可读则明确缺证。不再适用的 Skill 留在 excluded。来源或版本未知
不得伪造内容身份。三个恢复情境供独立消费检查，不能当作模型 A/B、原生宿主
自动恢复或 Token/费用改善的证明。其余已覆盖方法保留，避免重复增加规则。
