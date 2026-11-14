# 第四轮：Skill 的“净收益”与版本适配优先（2026-11-14）

本轮目标不是继续扩大 ADK 的 Skill 数量，而是减少**过期/错用 Skill 对实际任务的伤害**，并要求在原需求、真实项目与可执行验收下验证是否值得加载。所有外部项目均只读研究，未执行外部安装、hooks/MCP、模型/付费脚本或第三方评测器。下列 SHA 是**单文件 Git blob**，不是整仓 commit、再分发许可或安全认证。

| 核验来源 | 文件 blob SHA（短） | 重要方法 / 不可迁移处 | ADK 决策 |
|---|---|---|---|
| [SWE-Skills-Bench v2](https://github.com/ControllableModel/SWE-Skills-Bench/blob/main/README.md) | `README.md@922619aebcd7` | 固定真实仓库 commit + 需求 + hidden verifier，配对比较 `none/one`。其公开样本中多数收益有限，且存在版本过期引导风险；结果不能直接推定 ADK 的 65 Skills | **ENHANCE**：`adk-runtime-router` 先检查目标项目版本/显式任务限制，允许 no-skill；真实效果沿用 ADK `effect_trials` |
| [AgentSkillOS](https://github.com/ynulihao/AgentSkillOS/blob/main/README.md) | `README.md@0e54eeeac645` | 大规模 Skill 检索树和 DAG 编排面向高达数十万候选；当前 ADK 仅 65 项，已有唯一 Manifest/Router，迁移会加重维护 | **OBSERVE**：不引入第二套检索器/执行器 |
| [Microsoft Waza v0.41.0](https://github.com/microsoft/waza/blob/main/README.md) | `README.md@bf40aa02240f` | logical attempt / lineage / checkpoint 的冻结身份、复用和恢复；需要区分 2026-11-13 发行版与 main-only 命令 | **RETAIN**：现有 ADK Goal state/evidence 与恢复；不混入外部 CLI、不冒称运行可用 |

## 原 ADK 的缺口和本次改动

- `adk-runtime-router` 此前优先从候选触发开始路由，却缺少显式的 **target version fit**：Skill 引用可能来自旧 SDK、板级 BSP、框架或 API 版本。新增 Skill Fit Gate：命中只是候选，目标仓可信源码/当前用户验收优先；不适用时 `no-skill/abstain`，但仍完成轻量路由，不默默跳过。
- `adk-runtime-router/references/runtime-routing-details.md` 仅在跨版本冲突、需 fallback 或低置信度时加载，核 `user_acceptance / target_repo@commit / target_api_or_toolchain_version / skill_supported_scope / conflicting_guidance`，不让人肉治理取代生产 matcher。
- 已有 `adk-skill-composition-governance/references/skill-behavior-evaluation.md` 增加 Skill Value/Harm Gate：隔离初始 workspace，同一目标+需求+verifier 下成对比较，覆盖 wrong-version、explicit-instruction-conflict、irrelevant-trigger。只有真实 trace 才判 beneficial/neutral/harmful；否则 `not-measured`。
- 未新增 Skill、Agent、Runner、Schema、权限或模型训练任务；未修改 pre-registered holdout，避免污染盲评。新版 Skill 源码与 Matcher 契约在现有 PR 回归检查。

## 可复跑的反例设计（**仅设计、不是已执行模型实验**）

| 案例 | 应有行为 | 禁止行为 |
|---|---|---|
| FIT-01 | 用户指定当前 SDK 2.x、外部 Skill 引用 1.x API，先核项目 API 后决定是否加载 | 直接沿用过期示例覆盖项目代码 |
| FIT-02 | 已批准单文件修复，只需原回归，保留现有验收分母 | Skill 自带通用模板强迫新建完整规划 |
| FIT-03 | 对普通背景问答无合格 Skill，给 no-skill/abstain | 为增加激活率加载最接近的 Skill |
| VALUE-01 | 固定真实仓、任务、工具与 verifier 比较 with/without，并记任务差分和成本 | 把“加载成功”当成完成率提升 |
| VALUE-02 | Skill 使原本通过的任务回退，分类 harmful/待复审 | 仅看新增成功样例，忽视退化 |
| VALUE-03 | 只有源码路由/格式检查没有宿主轨迹，记录 not-measured | 把 E0/E1 升格为 E2–E4 或声称节省 Token |

## 资格边界

源级质量与生产确定性 matcher 的回归属于 E0/E1；真正的原生发现/加载、任务完成、越权、Token/缓存、费用、耗时属于 E2–E4。未经真实测量不得宣称提升。外部论文与 README 的统计结论仅说明基准自己的条件，不等于 ADK 真实用户效果。
