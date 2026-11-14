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
3. `tests/run_all.sh`：将已有 `test_token_context_governance.sh` 提到完整回归前段，不改变 102 项分母或命令，只让长入口触发限额错误更早暴露。此前 PR #264 在第 40 多项才发现 Router 超过 5600 字节，本轮缩短入口至 5401 字节并保留限额。

## 验证边界

本轮仓库验证仅为 E0/E1（源码/真实确定性 Matcher/既有 CI）；E2–E4 真实宿主任务成功、Token/缓存成本、延迟等均 `not-measured`。不能用上游论文结论证明 ADK 自身增益，也不能用文档中列出的未运行设计案例冒充模型轨迹。无授权不发起付费执行、外部环境写入或新定时巡检。
