# global-dev-kit 生产就绪度审计报告

> 审计时间: 2026-05-05
> 审计方式: 真实执行脚本 + 逐层验证，非文档审查
> 审计结论: **不具备生产就绪条件，存在 4 个阻断级问题**

---

## 一、审计结论总览

| 维度 | 评级 | 说明 |
|------|------|------|
| 核心脚本可执行性 | ✅ 良好 | install/validate/workflow 端到端跑通 |
| 资产内容质量 | ✅ 良好 | Skill 60-95 行，结构完整 |
| Profile 分层 | ✅ 良好 | core=13, personal-core=16, embedded-fullstack=32 |
| 测试覆盖 | ⚠️ 一般 | 新增 4 测试全 PASS，但 2 个测试文件缺失 |
| 意图路由 | ❌ 阻断 | match 功能 0/7 命中率 |
| 资产完整性 | ❌ 阻断 | 3 个宣称的 skill 实际缺失 |
| 实际部署 | ❌ 阻断 | ~/.codex 零安装 |
| 文档一致性 | ❌ 阻断 | help 示例与实际参数不符 |

**最终判定: 不满足"研发团队拿来即用"的条件。**

---

## 二、阻断级问题（必须修复）

### 阻断-1: 意图路由完全不工作

**现象:** `devkit.sh match` 对所有中文输入返回 `match=false`

**测试结果:**
```
"需要澄清需求"    → gdk-requirements-triage:    ❌
"拆解这个任务"    → gdk-task-breakdown:         ❌
"写单元测试"      → gdk-unit-test-embedded:     ❌
"调试这个问题"    → gdk-systematic-debugging:   ❌
"准备提交代码"    → gdk-commit-pr-quality-gate:  ❌
"设计寄存器映射"  → gdk-register-map-design:    ❌
"我要写驱动"      → gdk-driver-bringup-checklist: ❌
命中率: 0/7
```

**根因:** 两层设计脱节
1. `skill_match.sh` 读取 SKILL.md 的 `triggers` 字段做子串匹配
2. triggers 写的是描述性句子（"收到模糊需求或跨团队需求时"），不是可匹配关键词
3. `manifest.yaml` 的 `routing` 表（21 条 intent_zh）存在但 match 脚本**完全不读取它**

**影响:** 用户无法通过自然语言找到合适的 skill，意图路由形同虚设。

---

### 阻断-2: 3 个 v2.0.0 宣称的 skill 实际缺失

**缺失清单:**
```
skills/interview-candidate/SKILL.md        → ❌ MISSING
skills/design-pattern-suggest/SKILL.md     → ❌ MISSING
skills/release-readiness-gate/SKILL.md     → ❌ MISSING
```

**影响:** CHANGELOG 和 manifest 中声明的 v2.0.0 资产不完整，安装这些 skill 会失败。

---

### 阻断-3: ~/.codex 从未被实际安装

**现象:** 当前开发机上 `~/.codex/skills/` 和 `~/.codex/agents/` 均为空。

**影响:** 整个 gdk 从未在真实 codex 环境中验证过，"生产级落地"停留在文档层面。

---

### 阻断-4: 文档与实现不一致

**现象:** `devkit.sh` help 输出的示例:
```
./scripts/devkit.sh propose --title '测试变更' --scope 'test'
```
实际需要的参数:
```
./scripts/devkit.sh propose --change <id> --title '标题'
```

**影响:** 新用户按文档操作会直接报错。

---

## 三、高优先级问题（应修复）

### 高优-1: 新增 optional skills 未被任何 profile 引用

**孤立资产:**
```
optional-skills/gdk-data-fetch/gdk-fetch-url-content/SKILL.md   → 无 profile 引用
optional-skills/gdk-data-fetch/gdk-email-imap-fetch/SKILL.md    → 无 profile 引用
```

**影响:** 即使使用 `embedded-fullstack` profile 安装，也不会包含这两个 skill。

---

### 高优-2: 2 个测试文件缺失但测试脚本返回 PASS

**缺失文件:**
```
tests/test_manifest.sh          → No such file or directory
tests/test_agents_profiles.sh   → No such file or directory
```

**根因:** 测试脚本用 `source` 加载，缺失时 `set -e` 未触发退出码。

**影响:** 测试套件报告全部 PASS，但实际上有 2 个测试从未执行。

---

### 高优-3: match 脚本不消费 routing 表

`manifest.yaml` 中精心设计的 21 条路由:
```yaml
routing:
  - intent_zh: "需求不清楚怎么办"
    primary_skill: gdk-grill-with-docs
  - intent_zh: "任务太大怎么拆"
    primary_skill: gdk-task-breakdown
  ...
```

`skill_match.sh` 完全不读取这个字段，只看 SKILL.md frontmatter。

---

## 四、正常工作的部分

### ✅ 核心流程
| 功能 | 状态 | 说明 |
|------|------|------|
| `install` | ✅ | 3 个 profile 安装均成功 |
| `validate --strict` | ✅ | 校验通过 |
| `convert → claude-code` | ✅ | 转换产物正确 |
| `catalog build` | ✅ | 目录索引生成 |
| `propose → apply → verify → review → archive` | ✅ | 工作流端到端跑通 |

### ✅ 测试套件
| 测试 | 状态 |
|------|------|
| test_anti_rationalization.sh | ✅ PASS (8/8) |
| test_profile_conflicts.sh | ✅ PASS |
| test_routing.sh | ✅ PASS |
| test_skill_dependencies.sh | ✅ PASS |
| test_install.sh | ✅ PASS |
| test_no_external_repo_refs.sh | ✅ PASS |
| test_optional_skills.sh | ✅ PASS |

### ✅ 资产质量
- **28 个 Core Skills**: 60-95 行，frontmatter 完整（name/description/triggers/non_triggers/inputs/outputs/constraints）
- **5 个 Agents**: 角色定位清晰，决策规则明确
- **9 个 Profiles**: 分层合理，conflicts_with 已配置
- **5 个 Templates**: 工作流控制模板齐全

---

## 五、修复路线图

### 阶段 A: 修复阻断问题（P0）

1. **重写 skill_match.sh** — 让它消费 manifest.yaml 的 routing 表，而不只是 SKILL.md frontmatter
2. **补齐缺失的 3 个 skill** — interview-candidate, design-pattern-suggest, release-readiness-gate
3. **执行 ~/.codex 真实安装** — 用 personal-core profile 安装并验证
4. **修复 devkit.sh help** — 更新示例与实际参数一致

### 阶段 B: 修复高优问题（P1）

5. **将 optional skills 关联到 profile** — 至少一个 profile 应包含 gdk-fetch-url-content
6. **修复测试脚本** — 创建缺失的 test_manifest.sh 和 test_agents_profiles.sh
7. **triggers 重写** — 将描述性句子改为可匹配的关键词短语

### 阶段 C: 生产验证（P2）

8. **在真实项目中试跑** — 用 gdk 完成一个完整的驱动开发流程
9. **收集使用反馈** — 哪些 skill 真正有用，哪些是摆设

---

## 六、评分

| 维度 | 得分 | 满分 |
|------|------|------|
| 架构设计 | 8 | 10 |
| 脚本工程 | 7 | 10 |
| 资产质量 | 8 | 10 |
| 功能完整性 | 5 | 10 |
| 实际可用性 | 3 | 10 |
| 文档准确性 | 4 | 10 |
| **综合** | **35** | **60** |

**结论: 当前处于"半成品"状态——骨架搭好、肌肉长了一半、神经系统（路由）瘫痪。需要完成阻断修复 + 真实部署验证后，才能称为"拿来即用"。**
