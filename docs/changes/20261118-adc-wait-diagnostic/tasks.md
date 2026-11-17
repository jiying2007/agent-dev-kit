# 一次性诊断任务与角色

- [x] coordinator：固定问题、基线、一次性触发、预算、隐私、资格与停止条件。
- [x] implement_snapshot_priority：仅新增tools/diagnostics/adc_wait_20261118.py；冻结SHA256 5026b1ef580dba8e0eba32d80240936ab38eb3a20524aea3bd09b0ed18d4086f，最终AST/Ruff及15项隔离synthetic通过。D-1仅源码确认、D-2同验收实际RED/GREEN，夹具与记录工具错误均保留。
- [x] coordinator：仅新增专用workflow；只读审查已核无主线/发布写能力，最终包装仍核原路径字节漂移。
- [ ] independent_review：只读审完整新增内容、选择/退出码/隐私/预算及synthetic结果；通过前不推送实验分支。
- [ ] coordinator：一次受审树的分支push；不创建PR，不重试旧/新run，不修改tag或Root。
- [ ] audit：核实际job/source/log/artifact原件，按实证作诊断，不提前给源码修复或发行PASS。

当前状态：driver/workflow已实现，等待最终独立审查后才创建一次诊断分支头。本文件是执行前预注册；远端实际结果由该次job/artifact单独记录，不回写预期为历史事实。
