# 设计与取舍

参考 [GitHub Agentic Workflows 安全架构](https://github.github.com/gh-aw/introduction/architecture/) 对不可信内容和待审输出的分层处理；本地只吸收“显示内容不能变成结构或指令”的原则，不引入其 Action、检测器或写入 executor。

`evaluation.eval_markdown` 在拼接 Markdown 前，将动态值视为纯文本：非打印字符与换行折叠为空格，HTML 特殊字符实体化，Markdown 表格/链接/强调分隔符转义。摘要和任务行使用同一转换，避免只保护表格而让顶部元数据被换行伪造。原始 JSON 报告不改写；`status=pass` 的真实性仍由评测与独立证据核验。
渲染前还检查 report、results 和 latency 的基本对象形状；不符合时抛出 `ManifestError`，由既有 CLI 错误边界输出失败，不写出部分报告。

回滚只涉及渲染函数和负例测试，没有状态迁移。
