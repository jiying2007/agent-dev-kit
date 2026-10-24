# 设计

复用 `distribution/archive_io.py` 的有界读取与 release contract 的来源验证，基于受验证 source 和现有 target renderer/export manifest 形成预期输出，再对 bundle 的 target、路径、内容摘要、模式和数量进行校验。检查不得仅信任待验包内部可重写的摘要。

实现范围为 distribution owner、既有 target renderer/contract owner 与 release integrity 回归；不修改 shared schema、根 manifest、CI 或版本。主 Agent 串行整合版本与发布。回滚使用前一正式版本，不改写已发布资产。

契约迁移补充：既有 archive resource bounds、strict JSON 和 release manifest shell 回归的正向样例声明 direct target，却仅提供版本字段 source、没有 bundle。将这些正向样例迁移为真实最小可渲染 source 与 bundle，复用已有测试 helper；不为不完整样例添加 validator 豁免。

资源边界补充：release 重渲染经既有 renderer 的可选输出预算逐资产累计约束，避免有界输入被静态 frontmatter 重复放大。archive 首次读取后的同一 immutable bytes 作为临时 source 物化输入，避免重新打开可变路径；包内 Python 不执行，schema 只能离线解析。

独立审核扩展的信任边界：source inventory 只证明包内内容一致性，不让归档的 schema 或 Native registry 获得宿主权限。沿真实 renderer 调用链，对 manifest、target contract 和可达 Native receipt schema 复用同一离线 guard；support root 在任何 exists/rglob 前经原 ensure_within owner 校验。历史 renderer 与 target contract loader 之间用私有 Native verifier 许可参数区分原本机受管理调用与不可信归档重渲染：正常调用保持原默认，release 公共入口固定禁止。runtime conformance 在构造或执行 managed verifier 前失败关闭，不跳过 Native 验证，也不授予包内指定二进制或其自报 digest 执行权。当前两项正式 target 均为 static；今后如需接纳 runtime 归档，必须另行提供独立可信授权路径，不能通过本次接口绕过。

三项新负例分别证明 Native schema 曾请求外部引用、support root 曾先遍历源外目录、合法 Native receipt 曾到达归档指定的宿主 subprocess 调用。探针使用受控临时目录并拦截网络/进程执行，原始失败保留；修复后要求相应外部访问/执行调用次数为零，并继续验证静态包与正常本地 Native owner。

2026-10-24 历史检索负结果：`knowledge/L2-domain/lessons.md` 不存在。当前隔离环境无 `~/codex` Knowledge Provider / Execution Policy；记为环境 not-run，不能声称 live gate 通过。已有正式归档与审查反例为本变更输入。
