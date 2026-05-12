# Changelog

## v2.8.0 (2026-05-12)

### 修复
- manifest.yaml: 修复 33 个 skill 的重复 quality_tier YAML 键
- manifest.yaml: 补充 8 个缺失 Profile 定义 (personal-core, embedded-fullstack, team-core, openspec-driven, large-refactor, incident-response, research-intake, adk-artifact-gated-lite)
- 文档引用: 修复 7 个文件中的版本锁定引用 (统一为 2.8.0)
- 导航链接: 修复 NAVIGATION.md 3 个断裂 Runbook 链接
- Runbook 索引: 修复 runbooks/README.md 3 个错误文件名
- 脚本引用: 修复 check-global-codex-health.sh 和 check-adk-harden-readiness.sh 路径引用
- 统计数据: 更新 README.md 和 AGENTS.md 中的过时统计数字

### 统计
- Agents: 10 个
- Core Skills: 33 个
- Optional Skills: 9 个
- Profiles: 10 个 (新增 8 个)
- Scripts: 26 个

## v2.7.0 (2026-05-10)

### 增强
- VibeFlow 生命周期框架吸收 (8 阶段: Spark→Design→Tasks→Build→Review→Test→Ship→Reflect)
- Gate 机制设计原则 (4 问评估标准)
- 知识分层架构 (L0-L4) 文档化
- 仓库深度分析报告更新

### 新增
- docs/workflows/lifecycle.md: 生命周期工作流文档
- docs/workflows/gate-design.md: Gate 设计原则文档


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
- adk-data-fetch SKILL.md 创建

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
- 新增 Skill: adk-grill-with-docs, adk-diagnose-loop, adk-code-simplification, adk-context-engineering
- 新增 Skill: adk-chinese-commit-conventions, adk-chinese-code-review
- 新增 Optional Skill: adk-fetch-url-content, adk-email-imap-fetch
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

---

# 变更日志 - 1.0.0

## 版本信息
- 版本号: 1.0.0
- 发布日期: 2026-05-05
- 维护者: aiot03

## 变更内容

### 新增功能
- 完善使用指南和示例文档
- 增加最佳实践和故障排除指南
- 增加贡献指南
- 完善安装备份、回滚机制
- 增加健康检查和监控能力
- 增加版本锁定和升级路径

### 改进优化
- 增强测试覆盖
- 完善质量门禁
- 优化文档体系

### 已知问题
- 无

## 升级指南
1. 备份当前版本
2. 下载新版本
3. 运行健康检查
4. 验证功能

## 相关链接
- 文档: docs/
- 快速入门: docs/quick-start.md
- 故障排除: docs/troubleshooting.md
