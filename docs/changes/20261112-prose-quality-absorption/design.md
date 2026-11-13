# 设计与来源审查

## Provenance

- 启发来源：https://github.com/larashero3-dotcom/lieflat-less-ai-tone
- 阅读时 main SHA：fe77df00a27cf94428632ad449a4aecdcb83db41
- 公开许可：CC BY-NC 4.0（商业使用受限）；ADK 本仓库采用 MIT。
- 决策：method-only ENHANCE，采用一般化的编辑工作流独立编写；**没有复制或改写第三方源码、脚本、文段、规则表或语料**。未来若需直接集成上游检测程序或内容，必须先取得适用的商业授权并重新审查许可证。
- 上游实测样本缺原始语料可独立复算；仅作为方向性参考，绝不作为 ADK 语言质量保证、作者识别能力或用户文本统计显著性的证据。

## Architecture

- 单一可选能力 adk-prose-revision：在文件完成后使用，跟 adk-adr-writer（决策记录）和 adk-code-review-loop（代码审查）分责。
- 不改变 core profile、路由 IR 或 Root 子模块 pin；原有显式安装机制复用。
- 两种路径：仅诊断 report -> 精简定位建议；明确改稿 revise -> 最小修改、语义保真、简短差异说明。危险或不确定内容保留，不强制多轮确认。
- category=review_quality，专用 selection_group=prose-revision；workspace-write 只代表能力上限，实际写回仍取决于宿主权限与用户明确请求。
- 主入口短，反例按需读取，不移植脚本与评判模型；避免常驻 token、批量候选打标和无意义检查链。

## Risk / rollback / verification

- 风险：语义丢失、误改术语、引用变更、误认来源、许可侵权、额外 token。
- 抑制：固定不可变信息、保留不确定项、明确不做作者分类、method-only 独立内容；人工对照验收计划另行开展。
- 回退：从 optional_skills/typed contract 移除并删除独立目录及测试样例；不影响任何 core skill。
- 静态验证：manifest、catalog、frontmatter、trigger 正反例、可选安装；真实模型 A/B、误改率与 Token 成本 **not-measured**。
