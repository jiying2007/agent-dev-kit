# 第五轮外部方法吸收：结果优先评测、差分归因和验证经济性（2026-11-14）

本轮按可信来源核验**具体内容**，只读提炼方法，未安装第三方 CLI、hooks、MCP、技能包或执行付费模型。Git blob 仅冻结**单文件**身份，不构成版权/安全认证。以下方法改动均进入已有 ADK Skill 的按需 Reference，无新增运行时/评测引擎或全局常驻 Skill。

| 来源 | 证据 | 具体做法 | ADK 决策 |
|---|---|---|---|
| [Microsoft Eval Guide — eval-faq Skill](https://github.com/microsoft/eval-guide/blob/main/skills/eval-faq/SKILL.md) | `skills/eval-faq/SKILL.md@90079fec0af8` | 先以需求和最终状态判断正确性，再看工具选择、参数、必要性；只在合同明确时检查操作顺序，不能机械罚掉合法实现 | **ENHANCE**：已有 `skill-behavior-evaluation.md` 的 outcome-first grader，安全/授权仍为硬门禁 |
| [Microsoft Research — Agent Skills Can Be Harmful](https://www.microsoft.com/en-us/research/publication/agent-skills-can-be-harmful-an-empirical-study-of-skill-induced-failures-in-llm-agents/) | 2026-08 公开论文，非 Git 代码 | 307 个归因案例含 125 功能失败与 182 效率退化；多余验证与重型实施流程是具体风险 | **ENHANCE**：成对轨迹才作功能/效率归因；长任务按已验证快照复用阶段证据，不强制每一步完整 Goal |
| [NVIDIA SkillEvaluator](https://github.com/NVIDIA/SkillEvaluator/blob/main/skills/skillevaluator/SKILL.md) | `skills/skillevaluator/SKILL.md@5d6c5412b3fd` | 缺一侧轨迹/工具失败/不完整执行不能按有效的 Skill Lift 汇总，缺失分数不当作零 | **RETAIN+PRECISION**：ADK 现有 effect_trials/Run Evidence 继续权威；补 `invalid-eval / INCOMPLETE` 的结果披露 |
| [Anthropic — Demystifying evals](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 官方方法研究，非 Git 代码 | 任务必须让正确实现有机会通过 grader；保留成功/否定用例；人工审读 trace 以区分 Agent 错误和评测错误 | **RETAIN** 原有 train/holdout、独立 reviewer；本轮补 reference solution/grader 对照要求 |

## 具体落实

1. `optional-skills/adk-skill-composition-governance/references/skill-behavior-evaluation.md`：用原要求及真实工件 **outcome-first**，合法工具路径等价，不把“加载了 SKILL.md”当 no-skill 基线的通过项；以成对 trace 判功能/效率差异，缺失标无效，不造改善率。
2. `skills/adk-planning-execution-loop/references/long-task-recovery.md`：阶段低风险时，已验证同快照证据可有条件复用；依赖、工具授权、设备状态或正式 final 变化后重新走适用门禁，不借优化绕过审查。
3. `tests/run_all.sh`：将已有 `test_token_context_governance.sh` 提到完整回归前段，不改变 102 项分母或命令，只让长入口触发限额错误更早暴露。此前 PR #264 在第 40 多项才发现 Router 超过 5600 字节，本轮将入口恢复到 5600 字节以下并保留限额。

## 验证边界

本轮仓库验证仅为 E0/E1（源码/真实确定性 Matcher/既有 CI）；E2–E4 真实宿主任务成功、Token/缓存成本、延迟等均 `not-measured`。不能用上游论文结论证明 ADK 自身增益，也不能用文档中列出的未运行设计案例冒充模型轨迹。无授权不发起付费执行、外部环境写入或新定时巡检。

## 增量源码核查：champion/challenger 与短入口

- [OpenAI Skill Creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md) 单文件 blob `72bc0b97e7a6`：主入口只保留执行必要指令、额外参考按需读取，属于 **RETAIN/ENHANCE**。对应本轮 `adk-external-practice-absorption` 将四种模式压缩，消除与既有工作流重复的解释；没有增加 Skill 或常驻 Reference。
- [Skill-RSI — HOW_IT_WORKS](https://github.com/justinwetch/Skill-RSI/blob/main/docs/HOW_IT_WORKS.md) 单文件 blob `216de8ac1807`：同任务 champion/challenger 做小范围变化，稳定用例不能被探索新获益抵消，属于 **ENHANCE（方法）**，不是引入其循环执行器、模型评审或高成本研究包。
- [EvoSkill architecture](https://github.com/sentient-agi/EvoSkill/blob/main/docs/architecture.md) 单文件 blob `e7ff9d2feee1`：失败轨迹→单点假设→隐藏验证→保留最佳候选，作为 **OBSERVE**；不安装其 frontier/多分支执行、远程沙箱或自动生成技能。ADK 已有失败反馈、effect_trials 与 owner review，不创建并行平台。
- [Sentry Skill Writer iteration path](https://github.com/getsentry/skills/blob/main/skills/skill-writer/references/iteration-path.md) 单文件 blob `4a979365b938`：正负例和来源分类应分开记录，稳定已成功用例要防退化；既有生命周期方法已经覆盖，本轮 **RETAIN**，不复制模板。

### 已定位的执行前评测身份缺口

此前 `skill_method_ab_prereg.json` 仍登记 **11.2.16→11.2.17**，而当前候选已是 **11.2.18**。因两版均无实际模型评测，本轮将现用对照重绑为 `11.2.17@7aed1d... → 11.2.18@尚未合并`，原未执行方案保存在同一 JSON 的 `superseded_unrun_plan` 中。此为评测配置正确性修复，不是 A/B 结果。

**独立留出风险**：9 个原始案例的 5/4 分组虽然互不重叠，但内容在修订期间已被作者查看，因此只能算开发用例；未来真实晋级需独立方新建未曝光 holdout。champion/challenger 版本比较与 no-skill/with-skill 消融必须分别注册、证明真实 Skill exposure 并独立评审，不得拿不同 bundle digest 冒充目标 Skill 缺席。E2–E4 与实际 Token/成本仍为 `not-measured`，没有自动模型运行。
