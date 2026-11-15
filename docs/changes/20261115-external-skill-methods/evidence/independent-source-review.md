# 独立外源质量核验摘要

- 角色：独立只读研究与审查；没有修改 ADK 源码、需求或设计。
- ADK 基线：`5e0e83bcc127665de9a352e9eacfe9b092106cb2`，v11.3.3。
- 最近核验时间：2026-11-15 13:48:10 UTC（运行时 clock）。
- 范围：少量原始规范、Skill 入口、原始评测实现及反例；不是 65 项全库第三次作者审查。
- 未执行：外部 Skill、外部脚本、收费模型、native host、真实设备或用户工作区任务；全部模型效果 `not-measured`。

## 质量判断方式

分别判断格式可携带性、实际任务方法、工具/权限前提、原始测试覆盖和效果证据。目录收录、stars、字段齐全与已有 benchmark 文件均不等于任务增益。对每项机制先查当前 ADK 对应方法；没有可观察差距时保留现状。拒绝把第三方宿主命令、授权默认值和模型执行器隐式带入 ADK。

当前已读的 ADK 资产包括根规则、详细操作规则、技能格式指南、运行态模型、技能评测 runbook、外部吸收与深度分析入口、组合治理入口及行为评测 reference、context-engineering、target 渲染逻辑，以及前两轮 audit。现有 ADK 已具备成对 baseline/candidate、train/holdout 隔离、任务超时/基础设施失败区分、真实 trace 边界、非退化与成本比较；这些不是本轮新增缺口。

## 原始来源及判定

### AgentSkills 官方

- 仓库：`agentskills/agentskills@83021e2be457a9b6679148719c1f6074f0ad975e`。
- 实际获取：[client implementation](https://raw.githubusercontent.com/agentskills/agentskills/83021e2be457a9b6679148719c1f6074f0ad975e/docs/client-implementation/adding-skills-support.mdx)。SHA256：`e1a788f858766f4b54e0542e235ad3b1a965147e2c759926eb1c2b0a0129eef9`。
- 另实际打开 [format specification](https://agentskills.io/specification) 和 [evaluating-skills.mdx](https://github.com/agentskills/agentskills/blob/main/docs/skill-creation/evaluating-skills.mdx)；后者作为公开规范阅读，未把 main 链接冒充固定源码版本。
- 观察：client 文档明确允许 body-only 激活，所以 authoring frontmatter 中的 constraints/inputs/outputs 不能被假定总会进入模型上下文。技能目录位置和加载时机由宿主实现决定。
- 可取：三层按需加载、来源路径、明确 resource 基目录、去重加载和与宿主行为分离。
- 不直接取：blanket directory allowlist 与保护全部已加载 Skill 正文不受压缩只是宿主方案；不能自动获得 ADK 读写权限，也不宜把所有历史 Skill 永久留在活跃上下文。
- ADK 当前 target renderer 只将 target 指定 metadata 与正文导出；因此审查具体行为时应看最终正文/合同，而不是只看 authoring frontmatter。未在本次小样本中确认新的实现缺陷。

### Anthropic 官方

- 仓库：`anthropics/skills@1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064`。
- 实际获取：[run_eval.py](https://raw.githubusercontent.com/anthropics/skills/1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064/skills/skill-creator/scripts/run_eval.py)。SHA256：`43e3b8f80dbf69c343967ba77e268fae991d9fa3ed68b32a0ff02532cd48657f`。
- 实际打开 [skill-creator SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) 和 [upstream issue 1478](https://github.com/anthropics/skills/issues/1478)。issue 的问题不是直接当事实采纳；已核到固定版本脚本对应分支。
- 确认：脚本 future 异常会 append(False)，negative query 用低触发率判 pass；基础设施异常可能被评分成正确不触发。它还向共享 project_root 的 `.claude/commands` 写 UUID 探针，调用 `claude -p`。它测触发，不测完整任务交付。
- 判定：成对运行、真实产物评阅与可判别 assertion 可借鉴；runner 不导入，不以“官方脚本”替代评测方法审查。有关失败/有效分母的 ADK 方法已存在，不重复加治理流程。

### Sentry 实际工程仓

- 仓库：`getsentry/skills@a582c51ee29d0f35e6ac321340796f77d43da733`。
- 实际获取：[skill-evals.md](https://raw.githubusercontent.com/getsentry/skills/a582c51ee29d0f35e6ac321340796f77d43da733/skills/skill-writer/references/skill-evals.md)。SHA256：`6bba3ac97c78d66bd7df0c3b25ed153d43092c25588dfdb286f506b4930840f4`。
- 实际打开 [skill-writer SKILL.md](https://github.com/getsentry/skills/blob/main/skills/skill-writer/SKILL.md)。
- 可取：reference 带具体 open-when；先选最小执行形态；加规则前找需收窄/替换的已有内容；普通技能运行时不加载维护评测工件；holdout 不退化。
- 限制：该 eval reference 默认 AXIS、Codex adapter、full-auto；SPEC.md、registry 与参考目录属于其维护方式。不能整体复制为平台中立 ADK 的新依赖或强制多层流程。已有 ADK effect_trials 应复用。

### Trail of Bits 原始 tests/evals

- 仓库：`trailofbits/skills@149d7b21f4067765b82e67029730b42d228ef4b4`。
- 实际获取：[code-improver eval README](https://raw.githubusercontent.com/trailofbits/skills/149d7b21f4067765b82e67029730b42d228ef4b4/plugins/code-improver/evals/README.md)。SHA256：`c8770fcedfaffcfc5cf90b29b7bc3107029e5b2f0e3a1225b4360c5c59989372`。
- 可取：区分 outcome 与 artifact grader；验证 grader 真会对 known-bad specimen 失败；明确答案泄漏风险；以前版本结果不继承到重新泛化的新版本。
- 限制：README 明确当前重新命名与可插拔 reviewer 版本尚未完成新对照。旧版不产 ledger，所以 artifact 项按构造为零；不能据此宣称修错能力提高。实验付费且手工，不能自动导入。
- 实际获取：[check_contamination.py](https://raw.githubusercontent.com/trailofbits/skills/149d7b21f4067765b82e67029730b42d228ef4b4/plugins/code-improver/evals/check_contamination.py)。SHA256：`4566e34e92e66f3643882753185cf81f5d362044ac546ff476699be47023a002`。它在所有 agent trace 缺失但存在 judge explanation 时可 warning 后返回 0；没有逐 run 完整性保证，因此干净报告仍须说明观察覆盖。
- 实际获取：[continuity case](https://raw.githubusercontent.com/trailofbits/skills/149d7b21f4067765b82e67029730b42d228ef4b4/plugins/audit-context-building/evals/continuity-across-calls/case.yaml)。SHA256：`637fbe5d62e663bfa350560b5fd714da3422205adfc64e35037c5a3a09e17de6`。任务要求跨两层调用核实未兑现的前提，符合证据追踪方法；其中 [crossed-the-boundary grader](https://raw.githubusercontent.com/trailofbits/skills/149d7b21f4067765b82e67029730b42d228ef4b4/plugins/audit-context-building/evals/continuity-across-calls/graders/crossed-the-boundary.md) 只匹配 `decode_length`，不能单独证明分析正确。
- 根 LICENSE 已实读为 CC BY-SA 4.0，SHA256：`7abe19ec9bb73b36141b999b861d24ad855e808bafe0f81e84cce28556f6c297`。保持独立方法改写，不复制原文/代码。

## 后续独立合同审查关注点

本项是审核检查，不是实现设计：

1. 兼容迁移：清楚区分过渡兼容与永久镜像；破坏性收缩、数据迁移、真实发布分别保留授权、验收与回滚边界。
2. Property/stateful：从外部需求与不变量构造 oracle，保留合法/非法状态和最小可重放反例；不能将被测实现复制成模型后自证正确。
3. Sanitizer：明确实际编译器、目标、参数和 runtime 前提；报告类别与本次覆盖范围准确；一次 host 干净运行不是目标设备无未定义行为的证据。
4. 最终证据：源码摘要、时间戳、日志全量、独立身份、审查顺序、实际执行层次与来源适用性均需对应本轮 candidate；未运行保持 not-run/not-measured。
