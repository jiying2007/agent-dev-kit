# 第三方 Skill 安全扫描证据与误报复核（按需）

**适用**：`adoption preflight` 或 `install / runtime readiness`，而非单纯只读方法分析。扫描工具和模型均须经现有运行时授权，不自动安装/执行不可信目标的 scripts、hooks、postinstall 或远程代码。

1. 冻结来源：`candidate_source@commit/tag`、`skill_path`、LICENSE、依赖 lock 与可用的 target `SECURITY_MODEL.md@digest`。政策可能过期：逐项核真实符号/调用者和可访问入口，未核对不能给 `confirmed-safe`。
2. 列覆盖：`inspected/omitted/unavailable` 按 `SKILL.md / references / scripts / assets / symlink / hooks / MCP schema / install action / tool declarations / hidden/binary` 分类；扫描器不能读到的文件需说明原因和 owner，不以 0 findings 宣称 100% 覆盖。
3. 逐条扫描发现：`finding_id / pattern / source_symbol / input_trust / reachable_sink / affected_principal / resource / consequence / evidence / confidence / verdict`。对 prompt injection、数据外传、权限扩大、依赖污染、工具滥用与过度代理权分别找实际通路。没有可影响的 principal/resource/outcome 时标 `unverified` 或有反证的 `false-positive`，不凭关键词评分。
4. 独立判断：严重度、置信度、扫描覆盖率和真实利用条件分别报告；critical/high `confirmed` 阻断安装直到修复或正式授权的风险接受。不能因为 LLM 语义检查高分、无 CVE 或静态规则零命中就授予工具权限。
5. 回滚：记录 `tool_version / policy_rev / source_sha / allowed_scope / deny_path / sandbox / rollback`。源码审查合格只提供晋级候选；执行权限仍由宿主 policy 和 owner 控制。

本参考沿用已有 `adk-security-supply-chain` 的外部资产审查责任，不构成新 Skill 或第二套安全扫描引擎。
