# 综合分析：嵌入式 AI 工具实践 + Harness Engineering 对 llm_agent/adk 的优化启示

**分析日期**: 2026-05-13
**文章来源**:
1. [AI 是否会取代嵌入式工程师](https://mp.weixin.qq.com/s/42vL5RwXmN7O_gT_QeCh4w) - 嵌入式场景 AI 工具实践
2. [Harness Engineering：从 25% 到 90% 的 AI 代码率跃迁](https://mp.weixin.qq.com/s/rlIyIIZOXFObNIXbPI7gDg) - AI Coding 系统工程

---

## 一、两篇文章的核心观点提炼

### 1.1 嵌入式 AI 工具实践（文章一）

**核心观点**：短期不会取代，但不会用 AI 工具的嵌入式工程师会被甩开

**嵌入式场景的 4 个硬限制**：
1. 上下文窗口装不下"完整工程"（U-Boot + kernel + driver + rootfs = GB 级别）
2. 硬件交互是个黑盒（AI 没法接板子、看示波器）
3. 训练数据偏少且过时（冷门 SoC 的 datasheet AI 基本没见过）
4. 实时性/内存约束 AI 经常忽略（2KB 栈、中断里不能 sleep）

**ROI 最高的工具组合**：
- **第一档**：DeepSeek + datasheet、Claude Code 解析 BSP、AI 解释 kernel oops
- **第二档**：NotebookLM 知识库、自建 datasheet RAG、Continue + 本地模型
- **第三档**：团队共享 RAG 知识库、CI 集成 AI code review

**关键踩坑**：
1. AI 给的代码"看起来对"（编译能过、运行就崩）
2. 寄存器位定义"幻觉"（记混不同芯片的寄存器）
3. NDA 数据泄露风险
4. AI 让你"丧失基本功"
5. 中断/时序敏感代码偷懒

### 1.2 Harness Engineering（文章二）

**核心观点**：从 Prompt Engineering → Context Engineering → Harness Engineering

**四根支柱**：
1. **上下文架构**：分层加载，按需获取，控制在 40% 填充率以下
2. **Agent 专业化**：Planner/Generator/Evaluator 角色分离
3. **持久化记忆**：进度持久化在文件系统，非上下文窗口
4. **结构化执行**：理解 → 规划 → 执行 → 验证，每个阶段有质量门禁

**Agent 四种典型失败模式**：
1. One-shot Syndrome（试图一步到位）
2. Premature Victory Declaration（过早宣布胜利）
3. Premature Feature Completion（过早标记功能完成）
4. Cold Start Problem（环境启动困难）

**核心原则**：
> "If it can't be mechanically enforced, the agent will drift."

> "将做事的 Agent 和评判的 Agent 分开，是一个强有力的杠杆。"

---

## 二、两篇文章的交叉洞察

### 2.1 嵌入式场景是 Harness Engineering 的"困难模式"

| 维度 | 通用软件场景 | 嵌入式场景 | 对 Harness 的影响 |
|------|-------------|-----------|------------------|
| **上下文窗口** | 可以装下完整工程 | 装不下（GB 级别） | 需要更精细的上下文分层 |
| **硬件交互** | 纯软件，AI 可直接调试 | 黑盒，需要"人在环路" | 需要人工确认点更多 |
| **训练数据** | 充足 | 偏少且过时 | 需要 RAG 补充 datasheet |
| **实时性约束** | 不敏感 | 高度敏感 | 需要更严格的代码审查 |
| **失败成本** | 低（可回滚） | 高（可能损坏硬件） | 需要更严格的验证门禁 |

### 2.2 嵌入式场景的 Harness 必须更"保守"

文章一的核心教训：
> "AI 生成的代码经常编译能过、运行就崩——比如内核 API 用错了版本。"

文章二的解决方案：
> "Waiting is expensive, fixing is cheap"——宁可让 Agent 多跑一轮验证，也不要在人工 Review 时才发现问题。

**交叉洞察**：嵌入式场景的 Harness 应该：
1. **更严格的门禁**：不是"建议"而是"强制"
2. **更多的人工确认点**：关键决策必须人工确认
3. **更保守的验证**：不仅要编译通过，还要运行验证
4. **更完整的追溯**：每个变更必须有完整的审计链

### 2.3 嵌入式场景需要"专用 Harness"

文章一的工具分类：
- 通用对话型（Claude / DeepSeek / GPT）
- IDE / 编辑器集成（Cursor / Continue / Claude Code）
- 本地模型部署
- 专项工具（RAG、代码理解、文档生成、测试/仿真）
- Agent 化工作流（**当前不推荐**）

文章二的 Harness 设计：
- .harness/ 目录结构
- 十阶段开发流程
- 质量门禁可程序化验证

**交叉洞察**：嵌入式场景的 Harness 应该：
1. **优先专项工具**：RAG 知识库、代码理解、文档生成
2. **谨慎使用 Agent 化工作流**：只在 host 端、不碰交叉编译的场景
3. **强化人工确认**：关键决策必须人工确认
4. **渐进式引入**：从简单场景开始，逐步扩展

---

## 三、llm_agent/adk 优化建议

### 3.1 针对嵌入式场景的 Harness 设计

#### 3.1.1 上下文架构：三层加载 + 嵌入式专用层

```yaml
# manifest.yaml 增加嵌入式专用配置
embedded_context_layers:
  L1-always-loaded:
    description: 会话常驻层
    files:
      - AGENTS.md
      - docs/embedded-constraints.md      # 嵌入式硬限制
      - docs/hardware-interaction-rules.md # 硬件交互规则
    max_tokens: 4000

  L2-phase-triggered:
    description: 阶段触发层
    triggers:
      bsp-analysis:
        - skills/adk-bsp-porting-playbook/
        - knowledge/L2-domain/datasheets/  # datasheet RAG
      driver-development:
        - skills/adk-driver-bringup-checklist/
        - skills/adk-interrupt-dma-patterns/
      debugging:
        - skills/adk-systematic-debugging/
        - knowledge/L2-domain/oops-patterns/ # oops 模式库

  L3-on-demand:
    description: 按需查询层
    sources:
      - knowledge/L2-domain/datasheets/    # SoC datasheet
      - knowledge/L2-domain/errata/        # 芯片 errata
      - knowledge/L2-domain/bsp-history/   # BSP 历史
```

#### 3.1.2 质量门禁：嵌入式专用门禁

```bash
# scripts/quality-gates-embedded.sh

# 门禁 1: 内核 API 版本检查
check_kernel_api_version() {
    local code_file=$1
    local kernel_version=$2

    # 检查是否使用了错误版本的 API
    # 例如：Linux 6.x 改了的 API 不能用 4.x 的
    if grep -q "old_api_name" "$code_file"; then
        echo "FAIL: 使用了过时的内核 API，请检查内核版本 $kernel_version"
        return 1
    fi

    echo "PASS: 内核 API 版本检查通过"
    return 0
}

# 门禁 2: 中断安全性检查
check_interrupt_safety() {
    local code_file=$1

    # 检查中断处理函数中是否有禁用调用
    local forbidden_calls=("mutex_lock" "kmalloc.*GFP_KERNEL" "dev_info" "msleep" "usleep")

    for call in "${forbidden_calls[@]}"; do
        if grep -q "$call" "$code_file"; then
            echo "FAIL: 中断处理函数中发现禁用调用: $call"
            return 1
        fi
    done

    echo "PASS: 中断安全性检查通过"
    return 0
}

# 门禁 3: 寄存器位定义验证
check_register_bit_definition() {
    local code_file=$1
    local datasheet_ref=$2

    # 检查寄存器位定义是否与 datasheet 一致
    # 要求 AI 引用具体 datasheet 页码
    if ! grep -q "datasheet.*page" "$code_file"; then
        echo "WARN: 寄存器位定义未引用 datasheet 页码"
    fi

    echo "PASS: 寄存器位定义验证通过"
    return 0
}

# 门禁 4: 内存约束检查
check_memory_constraints() {
    local code_file=$1
    local stack_limit=$2  # 例如：2KB

    # 检查栈使用是否超过限制
    # 这需要静态分析工具支持
    echo "INFO: 内存约束检查需要静态分析工具支持"

    return 0
}
```

#### 3.1.3 Agent 角色：嵌入式专用角色

```yaml
# 在 agent-dev-kit/agents/ 下保留领域角色，在 skills/ 下保留能力型技能

# 1. BSP 分析师
bsp-analyst:
  description: BSP 代码分析、架构梳理、历史追溯
  default_skills:
    - adk-bsp-analysis
    - adk-bsp-porting-playbook
  responsibilities:
    - 梳理 vendor BSP 代码结构
    - 识别关键函数调用关系
    - 标出可能的设计问题
    - 分析 patch 历史
  constraints:
    - 必须引用 datasheet 页码
    - 必须标注置信度
    - 不确定的事实必须明示"待确认"

# 2. 驱动实现能力
adk-driver-implementation:
  description: 嵌入式驱动实现、联调验证与风险收口
  responsibilities:
    - 按 datasheet 编写寄存器读写代码
    - 实现中断处理函数
    - 编写 DMA 传输逻辑
  constraints:
    - 中断处理函数禁止 mutex_lock/kmalloc(GFP_KERNEL)
    - 外设访问必须设置超时和错误路径
    - DMA 路径必须处理映射、同步和回收

# 3. 硬件调试员
hardware-debugger:
  description: 硬件问题调试、oops 分析
  default_skills:
    - adk-hardware-debugging
    - adk-systematic-debugging
  responsibilities:
    - 分析 kernel oops/panic 信息
    - 定位硬件交互问题
    - 提出排查方向
  constraints:
    - 必须说明排查方向的置信度
    - 必须提供验证方法
    - 不能假设"应该可以工作"
```

### 3.2 针对通用场景的 Harness 设计

#### 3.2.1 变更管理：标准化目录结构

```bash
# 使用 agent-dev-kit/docs/changes/ 目录，并通过 manifest.yaml:change_sets 导出

docs/changes/
├── README.md                     # 变更管理说明
├── templates/                    # 变更模板
│   ├── summary-template.md       # 全流程追溯摘要
│   ├── spec-template.md          # 需求分析文档
│   ├── tasks-template.md         # 任务拆分清单
│   └── review-template.md        # 评审报告模板
├── examples/                     # 变更示例
│   └── add-modbus-tcp/
│       ├── summary.md
│       ├── request_analysis/
│       │   ├── spec.md
│       │   └── tasks.md
│       ├── coding/
│       │   ├── coding_report_v1.md
│       │   └── review/
│       │       └── code_review_v1.md
│       ├── unit_test/
│       ├── ci_result/
│       └── deployment/
└── README.md
```

#### 3.2.2 质量门禁：历史方案（已由 canonical change governance 取代）

以下片段是 2026-05 的分析快照，不是当前执行入口。当前请使用：

```bash
bash scripts/check-change-governance.sh docs/changes/<change-id>
```

```bash
# 历史草案：scripts/quality-gates.sh

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

#### 3.2.3 Agent 角色专业化分离

```yaml
# 硬切换后不保留 Planner/Generator/Evaluator 旧角色。
# 规划、实现、评估分别归入现有稳定角色和能力型 Skill。

# 1. 需求与任务规划
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

# 2. 实现执行
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

# 3. 验证与评审
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

---

## 四、实施路线图

### 4.1 第一阶段：嵌入式专用 Harness（1-2 周）

1. **创建嵌入式专用知识库**
   - datasheet RAG
   - oops 模式库
   - BSP 历史库

2. **创建嵌入式专用门禁**
   - 内核 API 版本检查
   - 中断安全性检查
   - 寄存器位定义验证

3. **创建嵌入式专用角色**
   - BSP 分析师
   - 驱动开发者
   - 硬件调试员

### 4.2 第二阶段：通用 Harness 增强（2-3 周）

1. **变更管理目录**
   - 标准化目录结构
   - 变更模板
   - 变更示例

2. **质量门禁可程序化**
   - CI 状态检查
   - 评审报告完整性检查
   - 文档同步检查

3. **Agent 角色分离**
   - Planner 角色
   - Generator 角色
   - Evaluator 角色

### 4.3 第三阶段：上下文架构优化（1-2 周）

1. **三层加载机制**
   - L1 会话常驻层
   - L2 阶段触发层
   - L3 按需查询层

2. **动态加载配置**
   - manifest.yaml 增加上下文配置
   - 按阶段自动加载/卸载

---

## 五、预期收益

### 5.1 嵌入式场景

| 维度 | 当前状态 | 优化后预期 |
|------|----------|------------|
| **代码质量** | AI 给的代码"看起来对" | 通过门禁拦截版本错误、中断安全问题 |
| **调试效率** | 靠经验找问题 | AI 辅助分析 oops、定位硬件交互问题 |
| **知识沉淀** | 散落在团队经验中 | datasheet RAG、oops 模式库、BSP 历史库 |
| **NDA 安全** | 存在泄露风险 | 本地模型 + 企业版 API 隔离 |

### 5.2 通用场景

| 维度 | 当前状态 | 优化后预期 |
|------|----------|------------|
| **需求理解** | Agent 经常误解需求意图 | 通过 spec.md + 用户确认点拦截偏差 |
| **编码质量** | 语法正确但业务逻辑有隐患 | 评审环节拦截潜在线上问题 |
| **测试覆盖** | Agent 往往跳过测试 | 产出有业务价值的测试用例 |
| **过程可追溯** | 无记录，全靠记忆 | 每个需求有完整变更文档链 |

---

## 六、核心结论

### 6.1 嵌入式场景的 Harness 必须更"保守"

> "AI 生成的代码经常编译能过、运行就崩。"

嵌入式场景的 Harness 应该：
1. **更严格的门禁**：不是"建议"而是"强制"
2. **更多的人工确认点**：关键决策必须人工确认
3. **更保守的验证**：不仅要编译通过，还要运行验证
4. **更完整的追溯**：每个变更必须有完整的审计链

### 6.2 质量门禁必须可程序化验证

> "If it can't be mechanically enforced, the agent will drift."

一切不可被机器验证的约束，在 Agent 执行中都是无效约束。

### 6.3 分离执行与评判是关键杠杆

> "将做事的 Agent 和评判的 Agent 分开，是一个强有力的杠杆。"

编码 Agent 和评审 Agent 的分离带来显著的质量收益。

### 6.4 流程一致性优先于流程效率

> "好的流程不应该给简单任务增加显著负担。"

保持流程一致性是一种廉价的保险。

---

## 七、参考资料

1. [AI 是否会取代嵌入式工程师](https://mp.weixin.qq.com/s/42vL5RwXmN7O_gT_QeCh4w)
2. [Harness Engineering：从 25% 到 90% 的 AI 代码率跃迁](https://mp.weixin.qq.com/s/rlIyIIZOXFObNIXbPI7gDg)
3. [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
4. [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/)

---

**分析完成时间**: 2026-05-13 09:30
**分析人**: AI 自动分析
**下一步**: 用户确认后开始实施
