# global-dev-kit 全面优化计划

> 基于 llm_agent 26 个子仓库深度分析结果
> 生成时间: 2026-05-05
> 当前版本: 1.0.0 (manifest) / 0.3.0 (README)
> 目标版本: 2.0.0
> 预计周期: 8 周（4 阶段）

---

## 目录

- [阶段一: 基础修复 (Week 1-2)](#阶段一-基础修复-week-1-2)
- [阶段二: 核心能力升级 (Week 3-5)](#阶段二-核心能力升级-week-3-5)
- [阶段三: 生态扩展 (Week 5-7)](#阶段三-生态扩展-week-5-7)
- [阶段四: 质量闭环与发布 (Week 7-8)](#阶段四-质量闭环与发布-week-7-8)
- [参考来源索引](#参考来源索引)
- [风险与约束](#风险与约束)

---

## 阶段一: 基础修复 (Week 1-2)

> 目标: 修复已知缺陷，统一配置冲突，建立基线

### 1.1 版本撕裂修复

**问题**: manifest.yaml 声明 version: 1.0.0，README 声明 0.3.0
**参考来源**: 自身分析
**动作**:
- 统一为 `2.0.0`（本次优化后的新版本）
- 在 manifest.yaml 和 README.md 同步更新
- 新增 CHANGELOG.md 记录版本历史

**验证**: `grep version manifest.yaml README.md` 一致性

---

### 1.2 配置冲突修复

**问题**: manifest `default_mode: symlink` vs README 推荐 `copy`
**参考来源**: 自身分析
**动作**:
- manifest.yaml 的 `install.default_mode` 改为 `copy`
- 保留 symlink 作为开发模式（`--mode symlink`）
- README 中明确区分"生产推荐(copy)"和"开发模式(symlink)"

**验证**: `grep default_mode manifest.yaml` 应显示 copy

---

### 1.3 Anti-Rationalization 机制引入

**问题**: Agent 容易跳过步骤、走捷径
**参考来源**: agent-skills（Anti-Rationalization 表设计）
**动作**:
- 为每个 p0 级 skill 添加 `## 合理化借口拦截` 章节
- 格式: 表格（借口 | 现实 | 正确做法）
- 首批覆盖 8 个 p0 skill

示例模板:
```markdown
## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "这个太简单，不需要测试" | 简单代码也会有边界条件 | 按 verification-before-completion 执行 |
| "我已经验证过了" | 口头验证不是证据 | 写入 Evidence Index |
```

**验证**: `grep -l '借口拦截' skills/*/SKILL.md | wc -l` 应为 8

---

### 1.4 Skill 路由表建立

**问题**: Agent 不知道何时调用哪个 Skill
**参考来源**: agent-skills（Intent→Skill 映射表）+ superpowers-zh（中文触发词路由）
**动作**:
- 在 manifest.yaml 新增 `routing` 字段
- 定义意图→技能映射（中英文双语）
- 支持主技能/支撑技能分层

示例:
```yaml
routing:
  - intent: "需求不明确/需要澄清"
    intent_zh: "需求不清楚"
    primary_skill: requirements-triage
    supporting_skills: []
  - intent: "准备提交代码"
    intent_zh: "要提交了"
    primary_skill: commit-pr-quality-gate
    supporting_skills: [verification-before-completion]
```

**验证**: `bash scripts/devkit.sh validate --strict` 通过

---

### 1.5 文档导航索引

**问题**: 42 个文档缺少统一导航
**参考来源**: codex_doc_cn（导航快照 + 差异对比）
**动作**:
- 创建 `docs/NAVIGATION.md` 统一导航
- 按类别分组: 用户文档 | 技术文档 | Runbooks | 变更记录
- 每个文档一行（路径 + 一句话描述）

**验证**: `test -f docs/NAVIGATION.md && echo OK`

---

## 阶段二: 核心能力升级 (Week 3-5)

> 目标: 引入参考仓的最佳实践，提升 gdk 核心竞争力

### 2.1 阻塞模板标准化

**问题**: 工作流缺少标准化的阻塞/交付模板
**参考来源**: artifact-gated-agents（BLOCKED/READY 模板 + 20 个 artifact 标签）
**动作**:
- 在 `templates/` 目录新增 `blocked.md` 和 `ready.md` 模板
- 在 `workflow.sh` 中集成阻塞检测逻辑
- 当缺少必要输入时自动输出 BLOCKED 模板

blocked.md 模板:
```markdown
# [BLOCKED] {{change_id}}

- status: BLOCKED
- owner: {{agent_name}}
- missing_inputs:
  - {{input_1}}
  - {{input_2}}
- blocking_reasons:
  - {{reason}}
- handoff_to: {{next_agent}}
- next_action: {{action_description}}
```

**验证**: `bash scripts/devkit.sh workflow verify` 支持 BLOCKED 状态

---

### 2.2 执行计划模板引入

**问题**: Runbook 缺少结构化的执行计划模板
**参考来源**: AUBB-Server（六要素: 目标/范围/风险/决策/验证/结果）
**动作**:
- 创建 `templates/exec-plan.md` 模板
- 更新所有 Runbook 引用此模板
- 在 workflow.sh 的 archive 阶段强制检查六要素完整性

模板结构:
```markdown
# 执行计划: {{title}}

## 1. 目标
## 2. 范围
## 3. 风险评估
## 4. 决策记录
## 5. 验证路径（含 Evidence Index）
## 6. 完成结果
```

**验证**: `grep -l 'exec-plan' docs/runbooks/*.md | wc -l` 应覆盖主要 runbook

---

### 2.3 质量评分卡

**问题**: 缺少量化的质量自评机制
**参考来源**: AUBB-Server（五维度评分卡）
**动作**:
- 创建 `templates/quality-score.md`
- 五维度: 架构(20%) | 可靠性(25%) | 安全(20%) | 产品(15%) | 文档(20%)
- 每个维度 0-100 分，含评分标准
- 集成到 workflow.sh 的 review 阶段

**验证**: `test -f templates/quality-score.md && echo OK`

---

### 2.4 Skill 健壮性模板

**问题**: 缺少统一的错误处理和重试机制
**参考来源**: skills/天工（retry/backoff/validate/quarantine 模板）
**动作**:
- 在 SKILL.md 规范中新增 `robustness` 章节要求
- 定义标准重试策略: retry(3次) + backoff(指数退避) + timeout(30s)
- 定义标准验证策略: validate(输入校验) + quarantine(异常隔离)
- 为 p1 级 skill 补充健壮性章节

**验证**: `grep -l 'robustness' skills/*/SKILL.md | wc -l` 应 >= 14

---

### 2.5 Skill 渐进式披露

**问题**: SKILL.md 内容过长，token 消耗大
**参考来源**: agent-skills（SKILL.md 入口 + references/ 按需加载）
**动作**:
- 每个 skill 的 SKILL.md 保持精简（<150 行）
- 详细参考资料移到 `references/` 子目录
- manifest.yaml 新增 `references` 字段声明

目录结构:
```
skills/systematic-debugging/
├── SKILL.md              # 精简入口（触发条件+核心流程）
└── references/
    ├── patterns.md       # 调试模式库
    └── checklist.md      # 检查清单
```

**验证**: `wc -l skills/*/SKILL.md | sort -n | tail -5` 最长不超过 200 行

---

### 2.6 Profile 冲突检测

**问题**: 两个 optional profile 叠加时无兼容性检查
**参考来源**: 自身分析
**动作**:
- 在 `check_profile_coherence.sh` 中新增冲突检测逻辑
- manifest.yaml 新增 `conflicts` 字段（声明互斥 profile）
- 检测: 同一 Agent 被两个 profile 以不同配置引入时的冲突

示例:
```yaml
profiles:
  release-hardening:
    conflicts_with: [incident-response]
    reason: "发布冻结期间不应同时做事故响应"
```

**验证**: `bash scripts/check_profile_coherence.sh` 检测冲突并报错

---

## 阶段三: 生态扩展 (Week 5-7)

> 目标: 扩展 gdk 的技能覆盖和多工具适配能力

### 3.1 新增工程方法论 Skill（从 agent-skills 吸收）

**参考来源**: agent-skills（grill-with-docs, diagnose, code-simplification）
**新增 Skill**:

| Skill | 来源 | 用途 | 质量层 |
|-------|------|------|--------|
| grill-with-docs | mattpocock-skills | 烤问式需求对齐 | p0 |
| diagnose-loop | agent-skills | 纪律化调试循环 | p0 |
| code-simplification | agent-skills | 代码简化（Chesterton's Fence） | p1 |
| context-engineering | agent-skills | 上下文工程优化 | p1 |

**验证**: `ls skills/{grill-with-docs,diagnose-loop,code-simplification,context-engineering}/SKILL.md`

---

### 3.2 新增中文场景 Skill（从 superpowers-zh 吸收）

**参考来源**: superpowers-zh（6 个原创中文 skill）
**新增 Skill**:

| Skill | 来源 | 用途 | 质量层 |
|-------|------|------|--------|
| chinese-commit-conventions | superpowers-zh | 中文 Git 提交规范 | p1 |
| chinese-code-review | superpowers-zh | 中文代码审查规范 | p1 |

**验证**: `ls skills/chinese-*/SKILL.md`

---

### 3.3 新增数据获取类 Skill（从 skills/天工 吸收）

**参考来源**: skills/天工（原子化 fetch + 三步工作流）
**新增 Skill**:

| Skill | 来源 | 用途 | 质量层 |
|-------|------|------|--------|
| fetch-url-content | skills | URL 正文提取 | p2 |
| email-imap-fetch | skills | IMAP 邮件获取 | p2 |

**新增 Optional Skill 目录**: `optional-skills/data-fetch/`

**验证**: `ls optional-skills/data-fetch/`

---

### 3.4 Profile 中文化增强

**问题**: Profile 全为中文描述，但缺少中文触发词路由
**参考来源**: superpowers-zh（中文触发词路由表）+ agency-agents-zh（本土化 Agent）
**动作**:
- manifest.yaml 的 routing 新增 `intent_zh` 字段
- 为每个 Profile 新增 `trigger_examples` 字段（含中文示例）

示例:
```yaml
profiles:
  embedded-fullstack:
    trigger_examples:
      - "我在做嵌入式开发"
      - "需要写驱动代码"
      - "要移植 BSP"
```

**验证**: `grep -c 'intent_zh' manifest.yaml` 应 > 20

---

### 3.5 Agent 交接协议模板

**问题**: Agent 间交接缺少标准化协议
**参考来源**: artifact-gated-agents（handoff_to + missing_inputs + next_action）
**动作**:
- 创建 `templates/agent-handoff.md`
- 定义标准交接字段: from_agent, to_agent, artifacts, status, blocking_items
- 在每个 Agent 的 AGENTS.md 中引用此模板

**验证**: `test -f templates/agent-handoff.md && echo OK`

---

### 3.6 Skill 依赖图声明

**问题**: Skill 间依赖关系未显式声明
**参考来源**: OpenSpec（Schema YAML 工件依赖图）
**动作**:
- manifest.yaml 的每个 skill 新增 `depends_on` 和 `enables` 字段
- 创建 `docs/skill-dependency-graph.md` 可视化依赖关系

示例:
```yaml
skills:
  - name: commit-pr-quality-gate
    depends_on: [verification-before-completion]
    enables: []
  - name: verification-before-completion
    depends_on: []
    enables: [commit-pr-quality-gate]
```

**验证**: `bash scripts/devkit.sh validate --strict` 检查依赖完整性

---

## 阶段四: 质量闭环与发布 (Week 7-8)

> 目标: 验证所有改动，补齐测试，发布 2.0.0

### 4.1 测试扩展

**动作**:
- 新增 `test_anti_rationalization.sh`: 验证每个 p0 skill 有借口拦截表
- 新增 `test_routing.sh`: 验证路由表完整性和意图匹配
- 新增 `test_skill_dependencies.sh`: 验证依赖图无循环
- 新增 `test_profile_conflicts.sh`: 验证冲突检测
- 更新 `test_skill_trigger_matrix.sh`: 覆盖新增 skill

**验证**: `bash tests/run_all.sh` 全部通过

---

### 4.2 生产脚本验证

**问题**: monitoring/auto-ops/performance/security 实现深度待验证
**动作**:
- 逐个审查 4 个脚本的实际功能
- 补充缺失的子命令实现
- 添加集成测试覆盖

**验证**: 每个脚本 `--help` 输出完整且子命令可执行

---

### 4.3 文档更新

**动作**:
- 更新 README.md: 版本号、新增 skill 列表、路由表说明
- 更新 docs/NAVIGATION.md: 覆盖新增文档
- 更新 docs/commands.md: 新增 routing 子命令
- 创建 CHANGELOG.md: 1.0.0 → 2.0.0 完整变更记录

**验证**: `rtk scripts/check-doc-sync.sh .` 通过

---

### 4.4 发布准备

**动作**:
- `bash scripts/devkit.sh validate --strict`: 全量验证
- `bash tests/run_all.sh`: 全量回归
- `bash scripts/devkit.sh install --tool codex --profile personal-core --mode copy --backup --install-report reports/release-2.0.0-report.md`: 生产安装验证
- 创建 Git tag: `v2.0.0`

**验证**: 所有门禁通过，安装报告生成

---

## 参考来源索引

| 改进项 | 参考仓库 | 借鉴内容 |
|--------|---------|---------|
| Anti-Rationalization | agent-skills | 借口拦截表设计 |
| Skill 路由表 | agent-skills + superpowers-zh | Intent→Skill 映射 + 中文触发词 |
| 阻塞模板 | artifact-gated-agents | BLOCKED/READY 模板 + 20 artifact 标签 |
| 执行计划模板 | AUBB-Server | 六要素(目标/范围/风险/决策/验证/结果) |
| 质量评分卡 | AUBB-Server | 五维度自评(架构/可靠性/安全/产品/文档) |
| 健壮性模板 | skills/天工 | retry/backoff/validate/quarantine |
| 渐进式披露 | agent-skills | SKILL.md 入口 + references/ 按需加载 |
| 中文触发词 | superpowers-zh | 中文场景路由表 |
| Agent 交接协议 | artifact-gated-agents | handoff_to + missing_inputs |
| Skill 依赖图 | OpenSpec | Schema YAML 工件依赖图 |
| 文档导航 | codex_doc_cn | 导航快照 + 差异对比 |
| Profile 冲突检测 | 自身分析 | 互斥 profile 声明 |

---

## 风险与约束

### 风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 新增 skill 质量不达标 | 降低 gdk 整体质量 | 每个 skill 必须通过 `validate --strict` |
| 路由表过于复杂 | Agent 选择困难 | 保持路由表精简（<30 条），fallback 到 core |
| Profile 冲突检测误报 | 阻塞合法组合 | 冲突声明为 warning 而非 error |
| 吸收外部 skill 引入依赖 | 增加维护成本 | 外部 skill 必须去外部仓库引用 |

### 约束

1. **不修改现有 p0 skill 的核心逻辑** — 只追加章节，不改变流程
2. **不引入外部运行时依赖** — 保持 bash-only
3. **不改变 devkit.sh 子命令接口** — 向后兼容
4. **每个阶段独立可验证** — 不依赖后续阶段完成

---

## 附录: 阶段验收检查清单

### 阶段一验收
- [ ] `grep version manifest.yaml` 显示 2.0.0
- [ ] `grep default_mode manifest.yaml` 显示 copy
- [ ] `grep -l '借口拦截' skills/*/SKILL.md | wc -l` >= 8
- [ ] `test -f docs/NAVIGATION.md` 通过
- [ ] `bash scripts/devkit.sh validate --strict` 通过

### 阶段二验收
- [ ] `test -f templates/blocked.md` 通过
- [ ] `test -f templates/exec-plan.md` 通过
- [ ] `test -f templates/quality-score.md` 通过
- [ ] `grep -l 'robustness' skills/*/SKILL.md | wc -l` >= 14
- [ ] `bash scripts/check_profile_coherence.sh` 支持冲突检测

### 阶段三验收
- [ ] `ls skills/grill-with-docs/SKILL.md` 存在
- [ ] `ls skills/diagnose-loop/SKILL.md` 存在
- [ ] `ls skills/chinese-commit-conventions/SKILL.md` 存在
- [ ] `grep -c 'intent_zh' manifest.yaml` > 20
- [ ] `test -f templates/agent-handoff.md` 通过
- [ ] `test -f docs/skill-dependency-graph.md` 通过

### 阶段四验收
- [ ] `bash tests/run_all.sh` 全部通过
- [ ] `rtk scripts/check-doc-sync.sh .` 通过
- [ ] `test -f CHANGELOG.md` 通过
- [ ] `git tag -l 'v2.0.0'` 存在
