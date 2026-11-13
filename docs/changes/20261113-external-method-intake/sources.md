# 2026-11-13 来源方法清单（非运行时依赖）
| 来源 | 吸收的方法 | 决策 |
|---|---|---|
| https://github.com/openai/skills | 短入口、references 按需加载、执行自由度分层 | ENHANCE 现有方法 |
| https://github.com/anthropics/skills | 正例/负例与真实行为迭代 | MERGE 已有 eval |
| https://github.com/microsoft/waza | 隔离 fixture 与评分器 | OBSERVE，无须新执行器 |
| https://github.com/obra/superpowers | 复现到完成前证据，不采信自述 | KEEP 已有门禁 |
| https://github.com/addyosmani/agent-skills | 过程纪律、避免合理化 | KEEP 已有工作流 |
| https://github.com/mattpocock/skills | 深度问答与领域词汇 | KEEP Explore/Challenge |
| https://github.com/trailofbits/skills | 假阳性验证、规格代码双向证据、补丁变体 | ENHANCE 审查思路 |
| https://github.com/getsentry/skills | Skill 安全检查、Prompt 源码与留出集 | ENHANCE 外部 intake |
| https://github.com/NVIDIA/skillspector | 注入、外传、权限、依赖风险分类 | OBSERVE，不引入扫描器依赖 |
| https://github.com/vercel-labs/agent-skills | 按影响排序、最低充分规则阅读 | KEEP 现有分层 |
| https://github.com/microsoft/skills | 专业领域按需装载，不全量加载 | KEEP 现有 profile |
这些是方法参考，不是第三方代码复制，也非已验证的 host 产品效果；source 结论与真实 Token 费用均 `not-measured`。
