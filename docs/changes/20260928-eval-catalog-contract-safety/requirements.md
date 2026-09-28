# 评测目录封闭字段与候选仓筛选

## 目标

静态评测目录不能接受未声明的 grader/fixture 字段或重复 JSON 字段；否则目录审计可能显示有效，后续消费者却读到隐藏的代码、命令或覆盖值。外部评测仓只作为方法候选，不改变 ADK Python 3.8 运行依赖。

## 验收

1. grader 只允许 `name/type/threshold`，fixture 只允许 `id/input/expected`；未知字段使目录审计失败。
2. 任意层级重复 JSON 字段使目录无效，不能声称 grader 或 runtime eval 已执行。
3. 现有 10 个 suite 的静态目录结果保持可用；真实 grader 与 provider 效果仍分别验收。
4. 新仓候选核官方来源、许可、Python/Node 门槛、安全边界和本地重复能力；无 exact 版本及独立决定前不导入资产、依赖或 runtime。

本批只保留本地未提交改动。
