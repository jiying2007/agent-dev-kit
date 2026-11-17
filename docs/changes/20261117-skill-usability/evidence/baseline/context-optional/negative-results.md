# Negative Results / 审查限制

基线：`78c3be7f6f9b5ee2e557de54156532fb3169198d`，2026-11-17 UTC。

## 已排除的产品缺陷假设

- **父 optional 会递归捆绑 IMAP 子 Skill**：实际 `render_selection` 的 Claude Code/OpenCode 父-only、URL-only、父+URL 三组对照均只包含显式选择项。没有发现该缺陷。详见 `probe-results.json -> optional_isolation`。
- **context 默认模板依赖未导出根 schema/template**：已有实际导出测试通过；两个 context Skill 的根帮助文件均已注明仅在已核源码根可选，默认模板自包含。
- **parallel 默认 reference 未跟随导出**：两个目标均保留默认任务信封及 review checklist，现有导出测试通过。
- **首次 Goal convergence 测试失败是源码问题**：首次 `PYTHONPATH=src` 的 module invocation 无法找到无包前缀的 `test_execution_policy`；修正为 `PYTHONPATH=src:tests` 后，仅重跑该模块，9 项通过。首次失败原文仍在 `tests-contracts.log`，成功在 `tests-goal-convergence.log`。
- **context 所有自动触发改成 token primary 必然为误路由**：当前内容合同明确 supporting/promotion，既有测试要求同组 primary，显式选 context 仍可用。仅记观察，不作新的修复要求。
- **Markdown worker 模板一定是坏的 v2 JSON**：直接字段转换被 typed validator 拒绝，但它是人类 Markdown 信封，没有声明 JSON schema。本轮只建议映射澄清，不把该设计反例称为已发生运行故障。

## 工具/入口负结果

- 一次组合搜索带入不存在的 `src/agent_dev_kit/rendering.py`，返回 rg exit2；随后通过源码符号定位到真实 `targets.py`。该失败不是产品结果。
- 一次预期 catalog 模块路径 `src/agent_dev_kit/catalog.py` 不存在；随后通过 rg 定位真实 `catalog_contract.py`。该失败不是产品结果。
- 一次预期 `manifests/intent_boundary_contracts.json` 不存在；canonical v2 校验器实际为 `src/agent_dev_kit/intent_boundary.py`，后续直接使用真实 validator。没有补造缺失文件。
- `render_selection(..., target="codex")` 按产品边界拒绝 direct export（external handoff only）。不是测试失败，也没有启用 Codex runtime；本轮消费者输出限于公开直接导出的 Claude Code/OpenCode。
- `probe_context_optional.py` 的消费者 catalog 命令 exit127 是 F-CO-02 的有效本地反例，原始 stderr 已保留，不能标为 validation pass。

## 没有运行的内容

- 未连接外部邮箱、公开网站、第三方扫描服务或模型服务。
- 未安装、发现或加载原生宿主 Skill；导出目录仅是隔离夹具。
- 未执行 SBOM/CVE/签名工具，也未运行未知候选的脚本、hooks/postinstall。
- 未运行完整仓库回归；本轮只读审查没有源码改动，仅执行能回答具体疑点的已有定向测试。
- 未测真实 task success、Token、缓存、延迟、交接质量和多Agent实际增益。
