# 2026-09-28 工作树自审

- Review Target：ADK `working-tree`；Reviewer Independence：`author-self-review`。需求基线为本目录 `requirements.md`、`design.md`；没有第三方代码导入或受控生命周期操作。
- Finding 1（major，已修复）：五条本地方法来源包含三组历史仓库别名，无法从旧 URL 直接对应根仓当前受管 pin。现行 URL 已按根仓只读审计对齐，旧 URL 作为 `historical_url` 保留；pin 与 HEAD 只代表 2026-09-28 元数据观察，未核祖先关系。
- Finding 2（minor，已修复）：原 checker 只核 URL 语法，不核 exact pin/关系和同仓记录一致性；`--manifest` 读入也缺大小、symlink 与重复字段边界。已加离线约束、可选根仓 lock 对照和显式新鲜度门禁，Python 3.8 正负例 7/7。
- 机械证据：规范来源 7/7；隔离根仓真实 `reference_pins.json` 的 URL/pin 对照与当天观察期限通过。当前 Python 3.8 quick 53 项中 52 项通过，唯一失败为 dirty 工作树 clean commit 身份门禁，内部 3 项通过；严格校验、release check、生态标准、退役引用和格式检查通过。
- Spec Verdict：本地声明合同按已观察元数据符合需求。Quality Verdict：缺独立 reviewer 与当前 full/clean commit 证据。Final Verdict：`needs-fix`（交付门禁未闭环）。

离线 checker 验证的是声明内部一致性，不认证远端仓库、许可或方法内容；远端观察不得自动提升为 pin、采纳或运行时批准。
