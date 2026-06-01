# Harness Engineering 对 llm_agent/adk 的优化分析

**分析日期**: 2026-05-13
**文章来源**: [Harness Engineering：从 25% 到 90% 的 AI 代码率跃迁](https://mp.weixin.qq.com/s/rlIyIIZOXFObNIXbPI7gDg)
**分析目标**: 识别 Harness Engineering 理念对 llm_agent/adk 的优化机会

---

## 一、核心概念对比

### 1.1 Harness Engineering 四根支柱 vs adk 现状

| Harness 支柱 | adk 现状 | 差距分析 |
|--------------|----------|----------|
| **上下文架构** | 知识分层(L0-L4) + manifest.yaml | ✅ 已有基础，但缺少动态加载机制 |
| **Agent 专业化** | 多角色 Agent 定义 | ⚠️ 有角色但缺少 Planner/Generator/Evaluator 分离 |
| **持久化记忆** | Holographic Memory | ✅ 已启用，但缺少进度持久化文件 |
| **结构化执行** | VibeFlow 生命周期 + Gate | ✅ 已有，但质量门禁可程序化验证不足 |

### 1.2 .harness/ 目录结构 vs adk 现状

| .harness/ 要素 | adk 对应 | 优化建议 |
|----------------|----------|----------|
| `agents/` | `skills/` 目录 | 可以扩展为独立的 agents/ 目录 |
| `rules/` | `docs/best-practices.md` | 需要拆分为独立的规则文件 |
| `skills/` | `skills/` 目录 | ✅ 已有，结构良好 |
| `changes/` | `docs/changes/` + `manifest.yaml:change_sets` + `manifest-fragments/change_sets.json` | ✅ 已纳入声明式变更工件治理 |
| `mcp/` | `manifest.yaml:mcp_servers` + `manifest-fragments/mcp_servers.json` + `docs/runbooks/mcp-governance.md` | ✅ 显式声明；默认空清单，禁止隐式安装 MCP |

---

## 二、关键优化机会

### 2.1 🔴 高优先级：变更管理（Changes）

**状态**: 当前 adk 已使用 `docs/changes/` 作为变更工件目录，并通过 `manifest.yaml:change_sets` 纳入通用 handoff 治理。后续优化重点是补真实业务样例和更多自动化一致性检查。

**Harness Engineering 方案**:
```
{变更类型}-{需求名称}-{YYYYMMDD}/
├── summary.md                    # 全流程追溯摘要
├── request_analysis/
│   ├── spec.md                   # 需求分析文档
│   ├── tasks.md                  # 任务拆分清单
│   └── review/                   # 需求评审记录
├── coding/
│   ├── coding_report_v1.md       # 编码报告
│   └── review/
│       └── code_review_v1.md     # 代码评审报告
├── unit_test/                    # 单元测试报告
├── ci_result/                    # CI 验证结果
└── deployment/                   # 部署验证报告
```

**adk 当前结构**:
```yaml
change_sets:
  - name: adk-change-governance
    root: docs/changes
    archive_root: docs/changes/archive
    required_files:
      - proposal.md
      - design.md
      - tasks.md
      - checklist.md
      - negative-results.md
      - verify-report.md
      - review-report.md
```

### 2.2 🔴 高优先级：质量门禁可程序化验证

**问题**: 当前 adk 的质量门禁多为"建议"和"最佳实践"，缺乏机械化约束。

**Harness Engineering 核心原则**:
> "If it can't be mechanically enforced, the agent will drift."

**adk 优化建议**:

```bash
# scripts/quality-gates.sh - 可程序化验证的质量门禁

# 门禁 1: CI 状态检查
check_ci_status() {
    local change_dir=$1
    local ci_result="$change_dir/ci_result/ci_report.md"

    # 必须满足三个条件
    if [[ ! -f "$ci_result" ]]; then
        echo "FAIL: CI 报告不存在"
        return 1
    fi

    local status=$(grep "status:" "$ci_result" | awk '{print $2}')
    local total_tests=$(grep "total_tests:" "$ci_result" | awk '{print $2}')
    local passed=$(grep "passed:" "$ci_result" | awk '{print $2}')

    if [[ "$status" != "SUCCESS" ]] || [[ "$total_tests" == "0" ]] || [[ "$passed" != "$total_tests" ]]; then
        echo "FAIL: CI 验证未通过 (status=$status, tests=$total_tests, passed=$passed)"
        return 1
    fi

    echo "PASS: CI 验证通过"
    return 0
}

# 门禁 2: 评审报告完整性检查
check_review_completeness() {
    local change_dir=$1
    local review_dir="$change_dir/coding/review"

    # 必须存在评审报告且包含必填章节
    if [[ ! -d "$review_dir" ]]; then
        echo "FAIL: 评审目录不存在"
        return 1
    fi

    local latest_review=$(ls -t "$review_dir"/code_review_v*.md 2>/dev/null | head -1)
    if [[ -z "$latest_review" ]]; then
        echo "FAIL: 评审报告不存在"
        return 1
    fi

    # 检查必填章节
    local required_sections=("问题描述" "修改建议" "优先级分级")
    for section in "${required_sections[@]}"; do
        if ! grep -q "## $section" "$latest_review"; then
            echo "FAIL: 评审报告缺少必填章节: $section"
            return 1
        fi
    done

    echo "PASS: 评审报告完整性检查通过"
    return 0
}

# 门禁 3: 文档同步检查
check_doc_sync() {
    local change_dir=$1

    # 检查代码变更是否同步更新了文档
    local coding_report=$(ls -t "$change_dir/coding"/coding_report_v*.md 2>/dev/null | head -1)
    if [[ -z "$coding_report" ]]; then
        echo "FAIL: 编码报告不存在"
        return 1
    fi

    # 检查是否包含文档更新记录
    if ! grep -q "文档更新" "$coding_report"; then
        echo "WARN: 编码报告中未找到文档更新记录"
    fi

    echo "PASS: 文档同步检查通过"
    return 0
}
```

### 2.3 🟡 中优先级：Agent 角色专业化分离

**问题**: 旧版 adk 曾使用 Planner、Generator、Evaluator 阶段型角色，容易与稳定职责角色重复。

**Harness Engineering 方案**:
- **requirements-analyst / architecture-planner**: 负责需求分析、任务拆解、方案设计
- **driver-engineer / component-engineer / application-engineer**: 负责编码实现、单元测试编写
- **test-validation-engineer / code-review-governor**: 负责代码评审、质量验证

**adk 优化建议**:

```yaml
# 硬切换后不保留 Planner/Generator/Evaluator 旧角色。
# 规划、实现、评估分别归入现有稳定角色和能力型 Skill。

# 1. 规划职责
requirements-analyst + architecture-planner:
  description: 需求分析、任务拆解、方案设计
  skills:
    - adk-requirements-triage
    - adk-task-breakdown
    - adk-interface-contract-design
  responsibilities:
    - 需求澄清与确认
    - 任务拆解与依赖分析
    - 方案设计与评审
  outputs:
    - spec.md
    - tasks.md
    - design.md

# 2. 实现职责
driver-engineer + component-engineer + application-engineer:
  description: 编码实现、单元测试编写
  skills:
    - adk-driver-implementation
    - adk-unit-test-embedded
  responsibilities:
    - 按规范编码实现
    - 编写单元测试
    - 生成编码报告
  outputs:
    - source code
    - unit tests
    - coding_report.md

# 3. 评估职责
test-validation-engineer + code-review-governor:
  description: 代码评审、质量验证
  skills:
    - adk-verification-before-completion
    - adk-code-review-loop
  responsibilities:
    - 代码评审
    - 质量门禁检查
    - 验证报告生成
  outputs:
    - code_review.md
    - verification_report.md
```

### 2.4 🟡 中优先级：上下文分层加载

**问题**: 当前 adk 的知识分层(L0-L4)是静态的，缺少动态加载机制。

**Harness Engineering 方案**:
- L1 — 会话常驻层：Agent 定义 + Rules
- L2 — 阶段触发层：按需加载 Skill
- L3 — 按需查询层：Wiki 知识库

**adk 优化建议**:

```yaml
# manifest.yaml 中增加上下文加载配置
context_layers:
  L1-always-loaded:
    description: 会话常驻层
    files:
      - AGENTS.md
      - docs/best-practices.md
      - docs/workflows.md
    max_tokens: 4000  # 控制在 40% 填充率以下

  L2-phase-triggered:
    description: 阶段触发层
    triggers:
      propose:
        - skills/adk-requirements-triage/
        - skills/adk-adr-writer/
      apply:
        - skills/adk-code-simplification/
        - skills/adk-unit-test-embedded/
      verify:
        - skills/adk-verification-before-completion/
      review:
        - skills/adk-chinese-code-review/

  L3-on-demand:
    description: 按需查询层
    sources:
      - knowledge/
      - docs/
      - examples/
```

### 2.5 🟢 低优先级：Dry Run 机制

**问题**: 当前 adk 没有 Dry Run 机制，新流程上线前缺乏验证。

**Harness Engineering 经验**:
> "在拿真实需求使用 Harness 之前，应当用一个虚拟需求完整走一遍全流程。"

**adk 优化建议**:

```bash
# scripts/dry-run.sh - Dry Run 脚本

#!/bin/bash
# 用虚拟需求验证 adk 流程

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ADK_ROOT="$(dirname "$SCRIPT_DIR")"

# 创建虚拟变更
VIRTUAL_CHANGE="dry-run-test-$(date +%Y%m%d)"
CHANGE_DIR="$ADK_ROOT/docs/changes/$VIRTUAL_CHANGE"

echo "=== Dry Run 开始 ==="
echo "虚拟变更: $VIRTUAL_CHANGE"

# 1. 创建虚拟变更目录
mkdir -p "$CHANGE_DIR"/{request_analysis,coding/review,unit_test,ci_result,deployment}

# 2. 生成虚拟需求文档
cat > "$CHANGE_DIR/request_analysis/spec.md" << EOF
# 虚拟需求：Dry Run 测试

## 问题陈述
这是一个虚拟需求，用于验证 adk 流程。

## 需求描述
- 功能：测试 adk 的 10 阶段流程
- 范围：仅限于流程验证
- 非目标：不涉及实际代码变更
EOF

# 3. 生成虚拟任务清单
cat > "$CHANGE_DIR/request_analysis/tasks.md" << EOF
# 任务清单

## 任务 1: 流程验证
- [ ] 验证 propose 阶段
- [ ] 验证 apply 阶段
- [ ] 验证 verify 阶段
- [ ] 验证 review 阶段
- [ ] 验证 archive 阶段
EOF

# 4. 运行流程验证
echo ""
echo "=== 验证 propose 阶段 ==="
# ... 调用 workflow.sh propose

echo ""
echo "=== 验证 apply 阶段 ==="
# ... 调用 workflow.sh apply

echo ""
echo "=== 验证 verify 阶段 ==="
# ... 调用 workflow.sh verify

echo ""
echo "=== 验证 review 阶段 ==="
# ... 调用 workflow.sh review

# 5. 清理虚拟变更
echo ""
echo "=== 清理虚拟变更 ==="
rm -rf "$CHANGE_DIR"

echo ""
echo "=== Dry Run 完成 ==="
echo "所有阶段验证通过"
```

---

## 三、优化优先级矩阵

| 优化项 | 优先级 | 工作量 | 预期收益 | 状态 |
|--------|--------|--------|----------|------|
| 变更管理目录 | 🔴 高 | 中 | 高 | 待实施 |
| 质量门禁可程序化 | 🔴 高 | 中 | 高 | 待实施 |
| Agent 角色分离 | 🟡 中 | 大 | 中 | 待评估 |
| 上下文分层加载 | 🟡 中 | 中 | 中 | 待评估 |
| Dry Run 机制 | 🟢 低 | 小 | 中 | 待实施 |

---

## 四、实施建议

### 4.1 第一阶段：变更管理（1-2 天）

1. 继续压实 `docs/changes/` 变更工件目录
2. 维护 `manifest.yaml:change_sets` 与 `manifest-fragments/change_sets.json`
3. 更新 `workflows.md` 文档
4. 提供真实业务变更管理示例

### 4.2 第二阶段：质量门禁（2-3 天）

1. 创建 `scripts/quality-gates.sh` 脚本
2. 定义可程序化验证的门禁条件
3. 集成到现有工作流
4. 添加门禁检查到评审流程

### 4.3 第三阶段：Agent 角色分离（3-5 天）

1. 分析现有 Agent 角色
2. 设计 Planner/Generator/Evaluator 分离方案
3. 创建新的角色技能
4. 更新工作流文档

### 4.4 第四阶段：上下文分层（2-3 天）

1. 分析现有知识分层
2. 设计动态加载机制
3. 更新 manifest.yaml
4. 测试上下文加载效果

---

## 五、预期收益

### 5.1 质量维度

| 维度 | 当前状态 | 优化后预期 |
|------|----------|------------|
| 需求理解偏差 | Agent 经常误解需求意图 | 通过 spec.md + 用户确认点，偏差在评审阶段前被拦截 |
| 编码质量 | 语法正确但业务逻辑有隐患 | 评审环节拦截渠道判断缺失等潜在线上问题 |
| 测试覆盖 | Agent 往往跳过测试或写形式化测试 | 实际需求产出有业务价值的测试用例 |
| 过程可追溯性 | 无记录，改了什么全靠记忆 | 每个需求有完整的变更文档链 |
| 流程一致性 | 因人而异，因需求而异 | 流程无论需求大小一致执行 |

### 5.2 效率维度

- **返工减少**：从 3-5 轮人工 Review 降到 1 轮
- **知识沉淀**：变更文档构成活的"项目开发手册"
- **新人上手**：通过变更历史快速理解项目全貌

---

## 六、结论

Harness Engineering 的核心理念与 adk 的设计哲学高度一致，但 adk 在以下方面存在优化空间：

1. **变更管理**：需要标准化的变更目录结构和模板
2. **质量门禁**：需要可程序化验证的机械化约束
3. **Agent 角色**：需要明确分离 Planner/Generator/Evaluator
4. **上下文加载**：需要动态分层加载机制

这些优化不是推翻现有架构，而是在 adk 现有基础上补强，使其更符合 Harness Engineering 的最佳实践。

---

**分析完成时间**: 2026-05-13 09:00
**分析人**: AI 自动分析
**下一步**: 用户确认后开始实施
