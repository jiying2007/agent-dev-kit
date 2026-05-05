# 文档导航索引

> 自动生成于 2026-05-05 | 共 42+ 文档 + 26 Runbooks

## 用户文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 快速入门 | quick-start.md | 5 分钟上手 |
| 使用指南 | usage.md | 完整使用说明 |
| 命令参考 | commands.md | devkit.sh 子命令详解 |
| 故障排除 | troubleshooting.md | 常见问题解决 |
| 最佳实践 | best-practices.md | 生产使用建议 |
| 贡献指南 | CONTRIBUTING.md | 如何参与贡献 |
| Codex 集成 | codex-agents-integration.md | ~/.codex/AGENTS.md 配合 |
| 技能组合指南 | skill-composition-guide.md | Skill 组合策略 |
| 映射矩阵 | mapping-matrix.md | Agent/Skill/Profile 映射 |
| 参考采纳指南 | reference-adoption.md | 如何从参考仓吸收 |

## 技术文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 场景工作流 | workflows.md | 7+ 场景详细建议 |
| Agent/Skill 目录 | agent-skill-catalog.md | 全量资产索引 |
| 技能依赖图 | skill-dependency-graph.md | Skill 间依赖关系 |

## Runbooks (26 个)

| Runbook | 路径 | 场景 |
|---------|------|------|
| 生产部署 | runbooks/production-deployment.md | 安装/配置/验证 |
| Runtime Routing | runbooks/runtime-routing.md | 路由规则与冲突 |
| 上游吸收 | runbooks/upstream-intake.md | 参考仓评估与吸收 |
| 团队交付 | runbooks/team-delivery.md | 团队协作流程 |
| 计划执行循环 | runbooks/planning-execution-loop.md | 长任务管理 |
| 安全供应链 | runbooks/security-supply-chain.md | 第三方审查 |
| 兼容性矩阵 | runbooks/compatibility-matrix.md | 工具兼容性 |
| Prompt 演进 | runbooks/prompt-evolution-delivery.md | 提示词优化 |
| 配置基线 | runbooks/config-baseline-governance.md | 配置管理 |
| Evidence Index | runbooks/evidence-index-delivery.md | 证据索引 |
| Codex Pilot | runbooks/codex-runtime-pilot.md | 运行时验证 |
| Lead Agent | runbooks/lead-agent-convergence-delivery.md | 主 Agent 收敛 |
| Skill 治理 | runbooks/skill-curation-delivery.md | 技能生命周期 |
| Spec Chain | runbooks/spec-chain-delivery.md | Spec 链路 |
| Codex Settings | runbooks/codex-settings-audit.md | 配置审计 |
| 迁移阶段 | runbooks/migration-stage-delivery.md | 渐进迁移 |
| 发布强化 | runbooks/release-hardening.md | 发布前检查 |
| 大平台交付 | runbooks/large-platform-delivery.md | 大型项目 |
| 跨团队交接 | runbooks/cross-team-handoff-delivery.md | 交接清单 |
| 功能交付 | runbooks/feature-delivery.md | 功能开发 |
| 重构强化 | runbooks/refactor-hardening.md | 重构流程 |
| 缺陷修复 | runbooks/bugfix-delivery.md | Bug 修复 |
| 变更桥接 | runbooks/openspec-bridge.md | 变更桥接 |
| Artifact 门禁 | runbooks/artifact-gated-delivery.md | 产物门禁 |
| 驱动调试 | runbooks/driver-bringup.md | 驱动开发 |

## 变更记录

| 文档 | 路径 | 说明 |
|------|------|------|
| 变更工件 | changes/ | 每个变更的 Evidence Index |
| 探索文档 | explorations/ | 探索性分析 |
| 规范文档 | specs/ | 技术规范 |

## 新增内容 (v2.0.0)

### 新增模板
| 模板 | 路径 | 说明 |
|------|------|------|
| 阻塞模板 | templates/blocked.md | 缺少输入时使用 |
| 交付模板 | templates/ready.md | 非阻塞产物交付 |
| 执行计划 | templates/exec-plan.md | 六要素执行计划 |
| 质量评分卡 | templates/quality-score.md | 五维度自评 |
| Agent 交接 | templates/agent-handoff.md | 角色间交接协议 |

### 新增 Skill (v2.0.0)
| Skill | 路径 | 来源 | 用途 |
|-------|------|------|------|
| grill-with-docs | skills/grill-with-docs/ | mattpocock-skills | 烤问式需求对齐 |
| diagnose-loop | skills/diagnose-loop/ | agent-skills | 纪律化调试循环 |
| code-simplification | skills/code-simplification/ | agent-skills | 代码简化 |
| context-engineering | skills/context-engineering/ | agent-skills | 上下文工程 |
| chinese-commit-conventions | skills/chinese-commit-conventions/ | 方法论 | 中文提交规范 |
| chinese-code-review | skills/chinese-code-review/ | 方法论 | 中文代码审查 |

### 新增可选 Skill (v2.0.0)
| Skill | 路径 | 来源 | 用途 |
|-------|------|------|------|
| fetch-url-content | optional-skills/data-fetch/ | skills/天工 | URL 正文提取 |
| email-imap-fetch | optional-skills/data-fetch/ | skills/天工 | IMAP 邮件获取 |

### 新增文档
| 文档 | 路径 | 说明 |
|------|------|------|
| Skill 格式指南 | docs/skill-format-guide.md | 渐进式披露规范 |
| Skill 依赖图 | docs/skill-dependency-graph.md | Skill 间依赖关系 |
| 变更日志 | CHANGELOG.md | 版本变更记录 |
