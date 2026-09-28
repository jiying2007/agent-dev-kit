# 2026-09-28 工作树自审

- Review Target：ADK `working-tree`；Reviewer Independence：`author-self-review`，不是独立审查。需求基线为本目录 `requirements.md` 与 `design.md`；受控生命周期操作不适用。
- 来源身份问题（major，已修复）：旧实现对输入/标签先 `sha256_file`，之后再次按路径解析。现在只对已读取的有限字节核 hash 并解析；读取后修改临时路径的负例证明本次结果仍绑定捕获字节。
- 边界负例（已修复）：输入/标签各自超预算及 symlink 均拒绝，现有 24 例正常路径通过；跨文件/manifest 原子性仍为 `false`。
- 机械证据：Python 3.8 `test_effect_eval.sh`、`test_software_m5_ready.sh`、严格校验、release check、模块体积、格式和差异检查通过；当前 quick 52 项中 51 项通过，唯一失败是未提交工作树的 runtime bundle clean commit 身份门禁，内部 3 项功能测试通过。
- Spec Verdict：按本地 source/test 边界符合需求。Quality Verdict：当前定向和 quick 已复验，full 当前快照与 fresh independent review 待集中收口。Final Verdict：`needs-fix`（交付身份与独立复审未完成）。
