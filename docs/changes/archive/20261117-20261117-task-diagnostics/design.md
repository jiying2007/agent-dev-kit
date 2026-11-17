# 设计说明：20261117-task-diagnostics

## 架构影响

设计者为 coordinator 与 read-only `audit_core`；实现者使用独立代理，不修改本契约。既有 `trace_summary.py` 提供纯函数 `diagnose_trace_summary(value)`，首先使用唯一的 `validate_trace_summary`，投影有限固定 finding codes、事实位置、原状态及已有 evidence refs。所有失败和缺测项保留，不使用模型、网络、时间或随机值，不修改输入。

既有 `evaluation_cli.py` 为 `eval import-task` 增加 `--diagnostics`。`import_task_evidence → read_task_evidence → _read_task_evidence → _import` 只增加默认 false 的 keyword 参数。生成既有 RunEvidence 后，使用同次已核验 `_Ledger` 补充实际 attempt 数、已记录 model-call 数和工具终态计数，以及 trace/events refs；仅显式请求时增加外层 `diagnostics`。`task_trials.py` 保持默认路径。

## 数据与配置影响

不新增 schema、持久状态、支持模块或依赖。Trace v2、RunEvidence、receipt、measurement、资格字段不变。诊断是现有报告的可选展示投影。导入器接线需保持 30000 bytes 模块预算；主体放在既有 trace_summary。严格 JSON、4 MiB 单文件、32 MiB 包、128 个文件、4096 个事件、no-follow 读取和 read-set/输出保护全部继承。

计量 unavailable 保留原原因，不将估算视作实测；合法零值保留。工具重复次数不等于无新证据重复；墙钟不等于并行等待。已有 repository certification 的调用方过程字段仍由原合同判断，诊断不能自动填充它们。

## 兼容性与迁移方案

新增兼容 CLI 功能发布为 11.4.0，无调用方迁移要求。无 flag 路径保持原报告。导入成功不等于任务成功，exit code 语义不变。回滚使用受保护 revert，并将 Root gitlink 恢复到已验证的 11.3.15；不改历史证据。

## 验证策略

验收驱动扩展既有 test_trace_summary.py/test_task_evidence.py，覆盖 requirements 的反例、CLI、输入/输出保护及资格不升格。AAR Skill 只增强现有 reference 与发现路径，并按 test_skill_content_contract.py 的既有字节一致契约同步 templates/memory/after-action-review.md，运行方法/路由/预算静态验证，不声称模型效果。共享发布门要求完整回归、strict validation、export、release check，以及独立 Spec/Quality 复核。
