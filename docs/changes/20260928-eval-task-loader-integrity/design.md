# 设计与来源

上一批参考 [Langfuse 数据集版本化](https://github.com/langfuse/langfuse-docs/blob/main/content/docs/evaluation/experiments/datasets.mdx) 和 [OpenAI Agents SDK Testing](https://openai.github.io/openai-agents-python/testing/) 建立输入身份与测试范围分层。本次针对本地 `load_tasks` 补完整性门禁，不引入服务、SDK 或存储依赖。

原实现遇到 `limit` 立即停止解析，因此后续重复 ID 或畸形记录不可见；`limit=0` 还会返回首条任务。新实现先对整个有限字节文件解析、校验唯一性和任务数量，再只保留选中的前 N 条；`task_set_sha256` 仍仅摘要实际评分的有序序列。调用方在读取结束后得到结果，跨文件/运行时状态并非原子快照。
直接调用 `run_deterministic` 的序列另核对象类型、非空、数量和唯一 ID，避免绕过 JSONL 加载器后发生除零或重复计分；评分公式不变。

回滚只需恢复任务加载函数、负例与说明；无持久状态迁移。
