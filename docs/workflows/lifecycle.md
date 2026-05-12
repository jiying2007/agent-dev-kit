# 8 阶段生命周期工作流

> 来源: VibeFlow 子仓吸收 (2026-05-12)
> 状态: 已落地

## 概述

本文档定义了 adk 的 8 阶段生命周期框架，用于组织和管理 AI 驱动的软件交付流程。

## 生命周期定义

```
Spark → Design → Tasks → Build → Review → Test → Ship → Reflect
```

## 阶段详情

### 1. Spark（需求澄清）

**目标**: 澄清需求，验证价值

**输入**:
- 用户需求/问题描述
- 业务背景
- 约束条件

**输出**:
- 需求文档 (`docs/changes/<feature>/requirements.md`)
- 价值评估报告

**门禁**: 需求完整性检查
- 需求描述清晰
- 价值评估完成
- 约束条件明确

**相关 Skill**: `adk-requirements-triage`

### 2. Design（技术方案设计）

**目标**: 设计技术方案

**输入**:
- 需求文档

**输出**:
- 设计文档 (`docs/changes/<feature>/design.md`)
- 接口规范

**门禁**: 三维评审通过
- 价值评审：这个功能值得做吗？
- 工程评审：技术方案可行吗？
- 设计评审：用户体验合理吗？

**相关 Skill**: `adk-artifact-gating`

### 3. Tasks（任务拆解）

**目标**: 合同化任务拆解

**输入**:
- 设计文档

**输出**:
- 任务清单 (`docs/changes/<feature>/tasks.md`)
- 功能列表 (`docs/changes/<feature>/feature-list.json`)

**门禁**: 任务合同检查
- 每个任务有明确的输入/输出/验收标准
- 任务边界清晰
- 任务可独立验证

**模板**: `templates/artifacts/tasks-template.md`

### 4. Build（TDD 驱动开发）

**目标**: 测试驱动开发

**输入**:
- 任务清单

**输出**:
- 代码变更
- 单元测试
- 测试覆盖率报告

**门禁**: 测试覆盖率检查
- 单元测试通过
- 测试覆盖率 >= 80%
- 无阻塞性问题

**相关 Skill**: `adk-tdd-workflow`

### 5. Review（代码审查）

**目标**: 多视角代码审查

**输入**:
- 代码变更

**输出**:
- 审查报告
- 改进建议

**门禁**: 审查门禁
- 无阻塞性问题
- 代码质量达标
- 安全性检查通过

**相关 Skill**: `adk-review-workflow`

### 6. Test（系统测试）

**目标**: 系统测试与 QA

**输入**:
- 代码变更

**输出**:
- 测试报告
- QA 签收

**门禁**: 测试门禁
- 系统测试通过
- 性能测试达标
- 兼容性测试通过

**相关 Skill**: `adk-test-workflow`

### 7. Ship（发布部署）

**目标**: 发布部署

**输入**:
- 测试通过的代码

**输出**:
- 发布产物
- 部署记录

**门禁**: 发布门禁
- 发布产物完整
- 部署验证通过
- 回滚计划就绪

**相关 Skill**: `adk-release-workflow`

### 8. Reflect（复盘沉淀）

**目标**: 复盘沉淀

**输入**:
- 发布产物

**输出**:
- 复盘报告 (`docs/changes/<feature>/reflect.md`)
- 经验教训

**门禁**: 复盘门禁
- 复盘报告完成
- 经验教训沉淀
- 改进措施明确

## 状态持久化

### state.json 规范

工作流状态持久化到 `.adk/state.json`：

```json
{
  "version": "1.0.0",
  "feature": "login-module",
  "phase": "build",
  "mode": "full",
  "created_at": "2026-05-12T10:00:00Z",
  "updated_at": "2026-05-12T15:30:00Z",
  "artifacts": {
    "requirements": "docs/changes/login-module/requirements.md",
    "design": "docs/changes/login-module/design.md",
    "tasks": "docs/changes/login-module/tasks.md",
    "feature_list": "docs/changes/login-module/feature-list.json"
  },
  "gates_passed": ["spark", "design", "tasks"],
  "gates_pending": ["build"],
  "history": [
    {
      "phase": "spark",
      "entered_at": "2026-05-12T10:00:00Z",
      "exited_at": "2026-05-12T11:00:00Z",
      "gate_result": "pass"
    },
    {
      "phase": "design",
      "entered_at": "2026-05-12T11:00:00Z",
      "exited_at": "2026-05-12T13:00:00Z",
      "gate_result": "pass"
    }
  ],
  "metadata": {
    "author": "leiwenjun",
    "priority": "high",
    "tags": ["auth", "security"]
  }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| version | string | 是 | state.json 版本 |
| feature | string | 是 | 功能名称 |
| phase | string | 是 | 当前阶段 |
| mode | string | 否 | 模式: full/quick |
| created_at | string | 是 | 创建时间 (ISO 8601) |
| updated_at | string | 是 | 更新时间 (ISO 8601) |
| artifacts | object | 是 | 产物路径映射 |
| gates_passed | array | 是 | 已通过的门禁 |
| gates_pending | array | 是 | 待通过的门禁 |
| history | array | 是 | 阶段转换历史 |
| metadata | object | 否 | 元数据 |

### 状态管理命令

```bash
# 初始化状态
adk lifecycle init --feature login-module

# 查询状态
adk lifecycle status --feature login-module

# 转换阶段
adk lifecycle transition --feature login-module --to design

# 绕过门禁（紧急情况）
adk lifecycle bypass --feature login-module --gate design --reason "紧急修复"

# 重置状态
adk lifecycle reset --feature login-module
```

## 快速模式

对于小型变更，支持快速模式：

```
Spark → Tasks → Build → Ship
```

### 快速模式条件

- 变更范围 < 3 个文件
- 不涉及架构变更
- 不涉及外部接口变更
- 用户明确指定快速模式

### 快速模式 state.json

```json
{
  "mode": "quick",
  "phase": "build",
  "gates_passed": ["spark", "tasks"],
  "gates_pending": ["build", "ship"]
}
```

## 中断恢复

### 恢复场景

1. **会话中断**: 用户关闭会话
2. **系统故障**: 系统意外重启
3. **人工暂停**: 用户主动暂停

### 恢复流程

1. 读取 `.adk/state.json`
2. 检查当前阶段
3. 检查已通过的门禁
4. 从当前阶段继续执行

### 恢复命令

```bash
# 恢复工作流
adk lifecycle resume --feature login-module

# 查看恢复点
adk lifecycle checkpoint --feature login-module
```

## 跨会话交接

### 交接场景

1. **多人协作**: 不同人处理不同阶段
2. **AI 接力**: 不同 AI 会话继续执行
3. **异步处理**: 长时间任务分批处理

### 交接流程

1. 当前执行者完成阶段
2. 更新 `state.json`
3. 通知下一个执行者
4. 下一个执行者读取 `state.json` 继续

### 交接命令

```bash
# 交接工作流
adk lifecycle handoff --feature login-module --to <next-executor>

# 查看交接历史
adk lifecycle history --feature login-module
```

## 与现有工作流的集成

### 与 propose-apply-verify-review-archive 的关系

8 阶段生命周期是更高层的抽象，propose-apply-verify-review-archive 是 Build 阶段的内部流程：

```
Spark → Design → Tasks → [Build: propose → apply → verify → review → archive] → Test → Ship → Reflect
```

### 与 artifact-gating 的关系

artifact-gating 协议为每个阶段提供门禁检查：

```
Spark (需求完整性检查) → Design (三维评审) → Tasks (任务合同检查) → Build (测试覆盖率) → Review (审查门禁) → Test (测试门禁) → Ship (发布门禁) → Reflect (复盘门禁)
```

## 参考

- VibeFlow 吸收报告: `reports/vibeflow-absorption-report-20260512.md`
- 状态机规范: `docs/workflows/state-machine.md`
- 门禁协议: `skills/adk-artifact-gating/SKILL.md`
