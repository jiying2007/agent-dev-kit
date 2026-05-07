# Changelog

## v2.6.0 (2026-05-06)
### 新增
- 脚本 smoke 测试：test_scripts_smoke.sh 覆盖 11 个脚本

## v2.5.0 (2026-05-06)
### 修复
- Trigger 冲突：修复 6 个 skill 的 trigger 重复
- Skills last_updated 日期更新为 2026-05-06

## v2.4.0 (2026-05-06)
### 修复
- manifest.yaml optional_skills 列表错误修正
- Docs 中 7 个脚本引用路径修正
- gdk-data-fetch SKILL.md 创建

## v2.3.0 (2026-05-06)
### 增强
- 10 个 Agents 全部充实（50-67L → 103-123L）
- 7 个 Optional Skills 全部充实（59-77L → 128-152L）

## v2.2.0 (2026-05-06)
### 增强
- 28 个 Core Skills 全部充实（65-106L → 80-195L）
- Skill 内容质量测试：test_skill_content.sh（196 检查点）

## v2.1.0 (2026-05-06)
### 增强
- Routing 全覆盖：28/28 skills
- user-story-template 扩充（29L → 235L）

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
- 新增 Skill: gdk-grill-with-docs, gdk-diagnose-loop, gdk-code-simplification, gdk-context-engineering
- 新增 Skill: gdk-chinese-commit-conventions, gdk-chinese-code-review
- 新增 Optional Skill: gdk-fetch-url-content, gdk-email-imap-fetch
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
