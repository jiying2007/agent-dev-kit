# Changelog

## v2.0.0 (2026-05-05)

### 新增
- Anti-Rationalization 机制：每个 p0 skill 添加"合理化借口拦截"表
- Skill 路由表：manifest.yaml 新增 routing 字段，支持中英文意图映射
- 阻塞模板：templates/blocked.md 和 ready.md
- 执行计划模板：templates/exec-plan.md（六要素）
- 质量评分卡：templates/quality-score.md（五维度）
- Agent 交接协议：templates/agent-handoff.md
- 健壮性规范：SKILL.md 新增 robustness 章节要求
- 渐进式披露：skill references/ 子目录支持
- Profile 冲突检测：manifest.yaml conflicts_with 字段
- Skill 依赖图：manifest.yaml depends_on/enables 字段
- 新增 Skill: grill-with-docs, diagnose-loop, code-simplification, context-engineering
- 新增 Skill: chinese-commit-conventions, chinese-code-review
- 新增 Optional Skill: fetch-url-content, email-imap-fetch
- 文档导航: docs/NAVIGATION.md
- 测试: test_anti_rationalization.sh, test_routing.sh, test_skill_dependencies.sh, test_profile_conflicts.sh

### 统计
- Agents: 10 个（不变）
- Core Skills: 28 个（+6）
- Optional Skills: 9 个（+2）
- Profiles: 10 个（不变，新增 trigger_examples）
- Templates: 5 个（新增）
- Routing: 21 条意图映射（新增）
- Tests: 25 个测试文件（+4）

### 修复
- 版本撕裂：manifest(1.0.0) vs README(0.3.0) 统一为 2.0.0
- 配置冲突：manifest default_mode 从 symlink 改为 copy

### 改进
- 42 个文档新增统一导航索引
- Profile 支持中文触发词路由（intent_zh + trigger_examples）
- 生产运维脚本验证和测试覆盖

## v1.0.0 (2026-05-02)

- 初始生产级发布
- 10 Agent + 22 Skill + 7 Optional Skill + 10 Profile
- Evidence Index 机制
- propose→apply→verify→review→archive 工作流状态机
- 24 脚本 + 21 测试文件 + 42 文档 + 26 Runbook
