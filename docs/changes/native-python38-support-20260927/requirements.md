# 需求：ADK 原生 Python 3.8 支持

## 目标

让当前 ADK 7.8.0 源码的全部公开 CLI、库 API、资产编译、target 检查、runtime bundle、release 准备与 Execution Policy 在 CPython 3.8.10 原生进程中运行，同时保持 Python 3.11/3.12 的现有结果与 fail-closed 语义。

## 边界

- 只修改 `agent-dev-kit` 的平台中立源码、依赖声明、测试和 CI；Codex 来源绑定与 live 应用必须等待 ADK 新的 clean commit 和证据。
- 不通过隐藏解释器切换、猴子补丁、修改已发布 wheel/tag、绕过 Schema 校验或降低信任门禁实现兼容。
- 保留现有工作树的 5 个隔离回归修复；不覆盖根仓参考目录、Codex 的本机安装备份或 Knowledge Hub 已有脏改。
- 静态质量工具可按解释器选择受支持的固定版本，但公开功能、完整行为测试与 release 检查在 3.8 必须执行。

## 验收

1. CPython 3.8.10 可安装源码并运行 `devkit.sh doctor`、`validate --strict`、全部测试、target static check、runtime bundle 与 release check；不得出现 import/syntax/依赖失败。
2. 同一源码在 3.11/3.12 的完整回归、路由与依赖审计不退化；Draft 2020-12 校验与信任负例保持 fail closed。
3. `requires-python`、构建后端、运行依赖、文档、CI 和测试矩阵一致声明 3.8；新发布版本必须有新的 clean commit、source/bundle hash，不能给旧 7.8.0 tag 改标签。
4. Codex 只在上游身份固定后重新导入并完成 build、doctor、plan、dry-run、apply、check；Knowledge Hub 只登记 reviewing 结论。

## 停止条件

- 3.8 兼容依赖不能保留既有 JSON Schema 或安全语义；
- 需要修改已发布精确源码却没有新的来源身份；
- 本机或 CI 验证只能靠跳过测试、伪造 receipt 或切换解释器通过。
