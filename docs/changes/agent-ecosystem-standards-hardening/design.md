# 设计说明：agent-ecosystem-standards-hardening

## 架构影响
- 不修改 compiler、target renderer、CLI 或 runtime；只扩展治理资产与静态验证。
- 来源决策仍由 `manifests/external_agent_pattern_contracts.json` 统一登记，实际约束落入现有领域 SSOT：
  - Agent Skills -> `skill_reproducibility_contracts.json`
  - OWASP ASI01-ASI10 -> `adk_runtime_policy_gates.json`
  - GitHub `gh-aw` safe-output -> `automation_worktree_contracts.json`
  - MCP Registry provenance -> `skill_mcp_dependencies.json`
  - OpenTelemetry GenAI -> `trace_eval_contracts.json`
  - ACP/A2A -> external ledger 的 watch-only contract
- 新增 `scripts/check-agent-ecosystem-standards.sh` 做跨 manifest 一致性校验，不承担业务执行。

## 数据与配置影响
- 所有变更均为 additive JSON 字段，既有 consumer 可忽略未知字段。
- 每个 adopted source 至少记录 `url`、`retrieved_at`、`review_status`、`expires_at`、`license`、`evidence_strength` 和 decision。
- Agent Skills 契约固定目录、`SKILL.md`、`name`、`description`、support files 和 progressive disclosure。
- ASI taxonomy 必须完整覆盖 ASI01-ASI10，并映射本地 control/evidence，而不复制 OWASP 正文。
- safe-output 强制 read-only agent、schema validation、独立 write executor、操作上限、kill switch、审计与回滚。
- MCP provenance 强制 namespace verification、version、digest、review/freshness 和 trust decision；registry listing 不等价于 trust certification。
- OTel adapter pin schema URL，默认不采集 prompt、completion、tool arguments/results 等敏感内容。
- ACP/A2A 只有版本、scope、复审触发器和 owner approval 字段，runtime 必须为 false。

## 兼容性与迁移方案
- 无 schema major bump：新增字段由新 checker 消费，现有资产渲染流程保持不变。
- checker 先作为 strict asset validation 的静态门禁；不触发安装、网络访问或 provider 调用。
- 回滚触发条件：现有 tests 发生非预期回归、旧 consumer 拒绝 additive fields，或任何外部 runtime 被启用。
- 回滚方式：撤销本 change 对 manifests/scripts/tests/fixtures/docs 的增量；没有外部副作用。

## 验证策略
- `rtk scripts/check-agent-ecosystem-standards.sh`
- `rtk scripts/check-agent-ecosystem-standards.sh --summary-json`
- `rtk tests/test_agent_ecosystem_standards.sh`
- `rtk scripts/validate-assets.sh --strict`
- `rtk tests/run_all.sh`
- `rtk scripts/check.sh`
- 通过标准：正向 bundle 通过；每个负向 fixture 精确命中预期失败；strict/full checks 退出码为 0；至少保留一条已验证负结果。
