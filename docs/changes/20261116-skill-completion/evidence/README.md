# 原始证据索引

`retained-files-index.json` 列出本轮保留的原始文件摘要、字节数和容器位置。各目录 `raw-evidence.json` 的 `files` 记录用 `path` 定位；按 `encoding` 解码 `content` 后重算 SHA256，可还原原始字节，包括失败日志、patch、报告的原始末尾换行。这样不会为通过格式检查而修改原始 patch 或日志。

| 位置 | 范围 |
|---|---|
| portfolio-audit.json | 65 个入口、53 个参考资源的基线/候选摘要和逐项处理 |
| general/raw-evidence.json | 40 项审计、真实导出/Git 反例、同一测试的 RED/GREEN 与原回归 |
| embedded/raw-evidence.json | 25 项审计、真实 CMake/timeout 反例、失败夹具、纠正运行、源码绑定及工具身份 |
| research/raw-evidence.json | 独立研究摘要、设计预审和 T3 独立原始报告/复跑；不是第三方全文 |
| research/source-index.json | 8 个原作者仓库的固定来源、blob/SHA/许可和负结果 |
| research/official-source-index.json | 两个官方 skill-creator 的具体入口及局部许可证身份 |
| consumer/raw-evidence.json | 新上下文执行者实际取得的导出 Skill、14 个输入、4 个结果及身份清单 |

历史 receipt 中的绝对路径保留其当时位置；原文件归档位置通过本索引解析，不要求这些临时路径永久存在。第三方来源索引的 raw locator 仅记录研究时的读取位置，原文未复制入仓；使用固定 URL/commit 可重新获取并核摘要。

consumer 是一轮对话中的四项定性任务，任务和输入由 root 准备，执行者未继承诊断/修复上下文。它没有旧版/无 Skill 对照、重复样本或 native host 测量，不能据此宣称成功率、Token/费用提升或产品资格。最终完整源码验证、独立裁决和平台发布见本 change 的后续 verification/review 及对应 GitHub 对象。
