# 设计：完整类型图与原始日志保真

设计/协调为 `ai/root`，五模块实现为 `ai/root/implement_task_evidence`，
只读独立复审为 `ai/root/review_existing_candidate`。

CI错误来自新增task模块把既有agent_value_contracts、agent_value_receipts、agent_value、
run_evidence、effect_trials纳入更完整的类型依赖图。改动限于callback参数/正确类型归属、
经现有验证后的字符串/映射窄化、datetime可空状态窄化和异质字典注解。
不改变统计公式、失败语义、授权或输入放行条件。

本地仅把src加入PYTHONPATH的mypy运行会把部分导入当作外部包，出现非等价绿灯。
复验使用完整CI清单与显式MYPYPATH源码解析，另直接检查全部五个问题模块，避免缓存/搜索路径掩盖。

原始first-integration.txt含测试框架空白行，直接作为新文本提交违反既有diff格式门禁。
改用first-integration.json的stdout_utf8保存原文，连同raw_bytes与raw_sha256；
反编码后必须与原日志完全一致，不删除失败、不改历史时间或102/101/1分母。
旧typed记录保持原字节，适用于原source/证据提交；其引用的历史文件在Git对象中保留。
本增量采用新的change与审查记录，绑定修复来源，不将历史记录视为当前字节的通过证明。
