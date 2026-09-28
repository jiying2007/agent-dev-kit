# 2026-09-28 工作树自审

- Review Target：ADK `working-tree`；Reviewer Independence：`author-self-review`，不是独立评审。需求基线为本目录 `requirements.md`、`design.md`；没有引入外部可执行资产。
- Finding 1（major，已修复）：原目录审计允许 grader/fixture 未知字段和 JSON 重复字段，后续消费者可能看到与静态审计不同的声明。现在封闭字段并拒绝重复键；对抗负例验证 `catalog_valid=false`，且未声称执行 grader。
- 来源候选：Pydantic Evals 与 Inspect AI 均为有价值的评测参考，但当前 Python ≥3.10；OpenAI Plugin Eval 是 Node.js 20+ 私有示例。三者仅作 review-required 方法线索，尚缺本轮 exact commit 和独立采纳决定。
- 机械证据：Python 3.8 目录测试 8/8；当前 quick 53 项中 52 项通过，唯一失败是 dirty 工作树 clean commit 身份门禁，内部 3 项通过。严格校验、release check、格式与模块体积门禁通过。
- Spec Verdict：静态目录与 runtime 未执行边界符合需求。Quality Verdict：当前定向和 quick 已复验；full 当前快照、候选 exact 来源和 fresh independent review 待收口。Final Verdict：`needs-fix`（交付身份与独立审查未完成）。
