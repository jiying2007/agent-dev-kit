# 本地任务

- [x] 核对 `eval_markdown` 对摘要和任务行的动态字段直接插值。
- [x] 增加纯文本转义，并用伪造完成字段、表格行、HTML 与链接样本验证。
- [x] 非对象报告、错误 results/latency 形状改为显式拒绝，负例通过。
- [x] Python 3.8 `test_software_m5_ready.sh` 定向测试与格式检查通过。
- [x] 既有历史 `deterministic-eval.json` 经 `devkit eval report` 正常渲染，旧报告缺新字段时显示 `n/a`；模块体积与严格校验通过。
- [ ] 当前快照整批回归、独立复审及 clean commit 身份留待统一收口；本阶段不提交、推送或 live apply。
