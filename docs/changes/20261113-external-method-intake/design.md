# 外部方法吸收 — 设计
基于 ADK 11.2.11，修改两处分析 Skill：`adk-skill-deep-analysis` 负责外部 Skill 方法与风险；`adk-repo-prompt-analysis` 负责 Prompt 实际调用链与信任边界。它们保持只读，没有自动写权限或第二路由权威。

原问题：单项分析也要求固定 5 维评分、三痛点、双图；Prompt 分析输出声称可直接更新采用矩阵，与 source-only 规则矛盾；仅靠 description/README 判断可能忽略源码、副作用与 Prompt 注入。修复为默认短路径、风险触发深审、真实行为只有经授权并冻结 baseline/holdout 才能认证。

无新增测试框架。复用现有 `tests/test_skill_content.sh` 运行源级反例，标准 PR CI/Release Gate 不变；不把来源字节节省称为运行时 Token 减少。
