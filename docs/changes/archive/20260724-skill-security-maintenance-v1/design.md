# 设计说明：skill-security-maintenance-v1

## 架构影响
- 复用 `skill_reproducibility_contracts.json` 承载 Skill 层安全与维护 evidence contract。
- 复用 `external_agent_pattern_contracts.json` 记录 OWASP AST10、Agent Skills 实证研究和 VS Code Agent Skills provenance/decision。
- 复用 ecosystem standards checker/fixture/test，不修改 portable Skill loader、target compiler 或安装器。

## 数据与配置影响
- `agentic_skill_security_taxonomy` 必须含 AST01-AST10，逐项具备 `local_surfaces/preventive_controls/evidence_required/residual_risk`。
- `skill-maintenance-evidence-v1` 必填 upstream revision/digest、stable behavior diff、target-local binding diff、use/effect、last verified、refresh/retire due 和 rollback。
- 使用效果未知时允许显式 `not-measured`，禁止用空字段或虚假计数代替。
- VS Code/GitHub Copilot watch entry 必须 `runtime_enabled=false`、`direct_target_added=false`，activation 需要真实 use case、版本 pin、export/install smoke、effect eval 和 rollback。

## 兼容性与迁移方案
- 不改变 `SKILL.md` frontmatter、manifest skill item 或目标编译格式。
- 新 evidence contract 只在外部派生、复用、晋级或定期治理时实例化；内部原生 Skill 不需要伪造 upstream。
- AST10 项目成熟度变化时更新 source status/crosswalk，不静默采用其 Universal Skill Format。

## 验证策略
- `rtk bash scripts/check-agent-ecosystem-standards.sh --summary-json`
- `rtk bash tests/test_agent_ecosystem_standards.sh`
- 负例：AST coverage 缺项、maintenance digest/retire 缺失、watch runtime enable、direct target 误新增。
- `rtk bash scripts/validate-assets.sh --strict`
- `rtk bash tests/run_all.sh --quick`
