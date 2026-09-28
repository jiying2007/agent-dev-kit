# 本地任务

- [x] 复核 8 个已批准参考仓远端：6 different、2 same、0 unavailable；只读且无 pin/checkout 写入。
- [x] 直接读取 Pydantic Evals、Inspect AI 与 OpenAI Plugin Eval 的官方仓库/许可/运行门槛，形成 review-required 方法候选。
- [x] 目录解析拒绝重复 JSON 字段，grader/fixture 拒绝隐藏字段；Python 3.8 定向 8/8 通过。
- [x] 当前 Python 3.8 quick 53 项中 52 项通过，唯一失败 `test_runtime_bundle` 需要 clean commit，内部 3 项通过；严格校验、release check、格式和模块体积门禁通过。
- [ ] 当前快照 full、候选 exact revision 核验和独立复审留待统一收口。
