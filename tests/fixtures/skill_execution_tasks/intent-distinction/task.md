# 区分明确执行和模糊探索

读取 requests。对两个请求输出 `decisions.json`，不得实际改实现。保留 requests 字节。第一项已有批准任务包且用户要求执行，不再重问已知事实；第二项产品与目标平台未知，选择一次能改变实施路径的澄清。

输出是按请求顺序的数组，每项 `request_id`、`mode`（execute-approved / explore）、`primary`、`questions`。questions 每项固定结构 `id`、`options`。本例唯一未决问题是 target-platform，选项 linux-embedded / mcu-rtos。没有未决问题时 questions 为空。使用现有 ADK planning-execution-loop 或 structured-requirements-questioning。
