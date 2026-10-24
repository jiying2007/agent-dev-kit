# 设计

复用 `distribution/archive_io.py` 的有界读取与 release contract 的来源验证，基于受验证 source 和现有 target renderer/export manifest 形成预期输出，再对 bundle 的 target、路径、内容摘要、模式和数量进行校验。检查不得仅信任待验包内部可重写的摘要。

实现范围为 distribution owner 与 release integrity 回归；不修改 shared schema、根 manifest、CI 或版本。主 Agent 串行整合版本与发布。回滚使用前一正式版本，不改写已发布资产。

契约迁移补充：既有 archive resource bounds、strict JSON 和 release manifest shell 回归的正向样例声明 direct target，却仅提供版本字段 source、没有 bundle。将这些正向样例迁移为真实最小可渲染 source 与 bundle，复用已有测试 helper；不为不完整样例添加 validator 豁免。

资源边界补充：release 重渲染经既有 renderer 的可选输出预算逐资产累计约束，避免有界输入被静态 frontmatter 重复放大。archive 首次读取后的同一 immutable bytes 作为临时 source 物化输入，避免重新打开可变路径；包内 Python 不执行，schema 只能离线解析。

2026-10-24 历史检索负结果：`knowledge/L2-domain/lessons.md` 不存在。当前隔离环境无 `~/codex` Knowledge Provider / Execution Policy；记为环境 not-run，不能声称 live gate 通过。已有正式归档与审查反例为本变更输入。
