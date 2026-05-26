# 知识分层架构

> 来源: 腾讯技术工程文章《Harness不是目的，知识才是护城河》
> 实施日期: 2026-05-12

## 概述

本文档定义了 adk 的五层知识存储架构，实现知识的精准组织和按需消费。

## 五层存储架构

```
knowledge/
├── L0-toolchain/            # Layer 0: 工具链配置知识
├── L1-general-tech/         # Layer 1: 通用技术知识
├── L2-domain/               # Layer 2: 业务领域知识
├── L3-project/              # Layer 3: 项目上下文
└── L4-session/              # Layer 4: 会话上下文（临时）
```

### Layer 0: 工具链配置知识

**定义**: AI 编码工具的配置、约定和最佳实践

**内容**:
- Codex/Claude Code/Hermes Agent/OpenCode 配置参考
- IDE 集成配置
- 工具链版本和兼容性

**示例**:
```
L0-toolchain/
├── codex-config.md          # Codex 配置参考，不作为 adk 默认运行时
├── runtime-config.md        # 通用运行时配置指南
├── claude-code-config.md    # Claude Code 配置指南
├── hermes-agent-config.md   # Hermes Agent 配置指南
├── ide-integration.md       # IDE 集成说明
└── toolchain-compatibility.md  # 工具链兼容性矩阵
```

### Layer 1: 通用技术知识

**定义**: 不依赖特定业务的通用技术知识

**内容**:
- 编程语言规范（C/C++/Python/Shell）
- 设计模式和架构模式
- 算法和数据结构
- 通用最佳实践

**示例**:
```
L1-general-tech/
├── c-coding-standards.md    # C 语言编码规范
├── cpp-best-practices.md    # C++ 最佳实践
├── shell-scripting-guide.md # Shell 脚本指南
├── embedded-patterns.md     # 嵌入式设计模式
├── rtos-concepts.md         # RTOS 概念
└── security-principles.md   # 安全原则
```

### Layer 2: 业务领域知识

**定义**: 特定业务领域的专业知识

**内容**:
- BSP 移植指南
- 驱动开发模式
- 协议栈集成
- 硬件调试技巧

**示例**:
```
L2-domain/
├── bsp-porting-guide.md     # BSP 移植指南
├── driver-development.md    # 驱动开发模式
├── i2c-spi-patterns.md      # I2C/SPI 通信模式
├── uart-protocols.md        # UART 协议集成
├── gpio-interrupt.md        # GPIO 中断处理
└── dma-optimization.md      # DMA 优化技巧
```

### Layer 3: 项目上下文

**定义**: 特定项目的历史决策、架构和约定

**内容**:
- 架构决策记录（ADR）
- 设计模式
- 历史决策和原因
- 项目特定约定

**示例**:
```
L3-project/
├── architecture-decisions/  # 架构决策记录
│   ├── adr-001-state-machine.md
│   ├── adr-002-gate-mechanism.md
│   └── adr-003-knowledge-layer.md
├── design-patterns/         # 项目设计模式
│   ├── lifecycle-pattern.md
│   ├── task-contract-pattern.md
│   └── review-dimension-pattern.md
└── historical-decisions/    # 历史决策
    ├── why-8-phases.md
    ├── why-vibeflow.md
    └── why-knowledge-layer.md
```

### Layer 4: 会话上下文

**定义**: 当前会话的临时状态和上下文

**内容**:
- 当前任务描述
- 临时笔记
- 会话状态

**示例**:
```
L4-session/
├── current-task.md          # 当前任务描述
├── session-notes.md         # 会话笔记
└── temp-findings.md         # 临时发现
```

**注意**: 此层内容不持久化，会话结束后清理

## 五种知识类型

### 1. 规则型 (Rules)

**定义**: 必须遵守的约束和规范

**位置**: `rules/`

**格式**: SKILL.md with constraints section

**示例**:
- 编码规范
- 安全规则
- 工作流规则

### 2. 模式型 (Patterns)

**定义**: 可复用的解决方案和设计模式

**位置**: `skills/`

**格式**: SKILL.md with workflow section

**示例**:
- BSP 移植模式
- 驱动开发模式
- 协议集成模式

### 3. 案例型 (Cases)

**定义**: 具体的实现示例和代码片段

**位置**: `templates/`

**格式**: template files

**示例**:
- 代码模板
- 配置示例
- 脚本模板

### 4. 经验型 (Experiences)

**定义**: 踩坑记录和最佳实践

**位置**: `docs/explorations/`

**格式**: negative-results.md

**示例**:
- 踩坑记录
- 调试经验
- 性能优化经验

### 5. 索引型 (Indexes)

**定义**: 知识的元数据和导航

**位置**: `docs/reference/`

**格式**: catalog.md, index.md

**示例**:
- 知识目录
- 导航索引
- 引用索引

## 三级成熟度

### 草稿 (Draft)

**定义**: 初始记录，未经验证

**特征**:
- 内容可能不完整
- 未经实践验证
- 可能有错误

**标记**: `maturity: draft`

### 验证 (Verified)

**定义**: 经过实践验证

**特征**:
- 内容完整
- 经过实践验证
- 可以使用

**标记**: `maturity: verified`

### 成熟 (Mature)

**定义**: 被广泛引用，稳定可靠

**特征**:
- 内容完整且稳定
- 被多次引用
- 经过时间验证

**标记**: `maturity: mature`

## 知识查询命令

```bash
# 按层级查询
adk knowledge query --layer L1

# 按类型查询
adk knowledge query --type patterns

# 按成熟度查询
adk knowledge query --maturity mature

# 按标签查询
adk knowledge query --tag embedded

# 组合查询
adk knowledge query --layer L2 --type patterns --maturity verified
```

## 知识沉淀流程

### 1. 工作流沉淀

在 8 阶段生命周期中自动沉淀知识：

```
Spark → 沉淀需求决策
Design → 沉淀设计决策
Tasks → 沉淀任务拆解经验
Build → 沉淀实现踩坑记录
Review → 沉淀评审洞察
Test → 沉淀测试发现
Ship → 沉淀发布经验
Reflect → 沉淀复盘教训
```

### 2. 手动沉淀

```bash
# 沉淀知识
adk knowledge add --layer L2 --type experiences --content "I2C 总线仲裁踩坑记录"

# 更新成熟度
adk knowledge update --id <id> --maturity verified

# 添加引用
adk knowledge cite --id <id> --from <source>
```

## 知识健康检查

```bash
# 检查知识健康
adk knowledge health

# 检查项：
# 1. 长期未引用的知识（>90天）
# 2. 过期的知识（>180天未更新）
# 3. 引用断裂（引用了不存在的知识）
# 4. 孤立知识（未被任何文档引用）
```

## 与现有架构的整合

### 与生命周期整合

```
8 阶段生命周期
    ↓
知识沉淀点
    ↓
knowledge/ 五层目录
```

### 与 Gate 机制整合

```
Gate 检查
    ↓
知识完整性检查
    ↓
知识质量评估
```

### 与 Skills 整合

```
Skills
    ↓
关联知识层
    ↓
按需消费知识
```

## 参考

- 腾讯技术工程文章: [Harness不是目的，知识才是护城河](https://mp.weixin.qq.com/s/JV4-oPP0jjsBCZ4tW3Gy1g)
- 分析报告: `docs/analysis/tencent-article-analysis-20260512.md`
- 生命周期文档: `docs/workflows/lifecycle.md`
