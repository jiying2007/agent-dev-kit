# CONTEXT.md — agent-dev-kit 领域语言定义

> 最后更新: 2026-05-16
> 版本: 2.8.0

---

## 1. 核心概念

### 1.1 Agent (代理)
- **定义**: 具有特定角色和职责的 AI 助手实例
- **位置**: `agents/<name>/AGENTS.md`
- **示例**: requirements-analyst, architecture-planner, driver-engineer

### 1.2 Skill (技能)
- **定义**: 可复用的、特定领域的知识和流程模块
- **位置**: `skills/<name>/SKILL.md` 或 `optional-skills/<name>/SKILL.md`
- **分类**:
  - **Core Skills**: 核心技能，必须具备可执行流程与验收证据模板
  - **Optional Skills**: 可选技能，仅在明确请求时安装

### 1.3 Profile (配置文件)
- **定义**: 预定义的 Agent/Skill 组合，用于特定场景
- **位置**: `manifest.yaml` 中的 `profiles` 部分
- **示例**: core, embedded-fullstack, release-hardening

### 1.4 Manifest (清单)
- **定义**: 单一事实源，定义所有 Agent/Skill/Profile 的元数据和依赖关系
- **位置**: `manifest.yaml`
- **作用**: 驱动安装、验证、转换等所有操作

---

## 2. 领域术语

### 2.1 嵌入式系统开发
- **BSP**: Board Support Package，板级支持包
- **RTOS**: Real-Time Operating System，实时操作系统
- **MCU**: Microcontroller Unit，微控制器
- **HIL**: Hardware-in-the-Loop，硬件在环
- **SIL**: Software-in-the-Loop，软件在环
- **DMA**: Direct Memory Access，直接内存访问
- **ISR**: Interrupt Service Routine，中断服务程序

### 2.2 质量门禁
- **Artifact**: 工件，开发过程中产生的文档、代码、测试等
- **Gate**: 门禁，质量检查点
- **Evidence**: 证据，验证结果的记录
- **Verification**: 验证，确认实现符合要求
- **Validation**: 确认，确认需求正确

### 2.3 工作流
- **Propose**: 提议，创建变更提案
- **Apply**: 应用，实施变更
- **Verify**: 验证，检查变更结果
- **Review**: 评审，人工审核
- **Archive**: 归档，保存变更记录

---

## 3. 质量等级

### 3.1 Quality Tiers
- **P0**: 核心主干资产，必须具备可执行流程与验收证据模板
- **P1**: 稳定扩展资产，必须具备命令、样例和质量门禁
- **P2**: 可选场景资产，必须具备边界说明和最小验证路径

### 3.2 质量评分
- **A+ (优秀)**: 95-100 分
- **A (良好)**: 85-94 分
- **A- (中上)**: 75-84 分
- **B+ (中等)**: 65-74 分
- **B (及格)**: 55-64 分
- **C (需改进)**: 45-54 分
- **D (不达标)**: <45 分

---

## 4. 工具目标

### 4.1 支持的工具
- **Codex**: OpenAI 的 AI 编程助手
- **Claude Code**: Anthropic 的 AI 编程助手
- **Hermes Agent**: 开源 AI Agent 框架
- **OpenCode**: 开源 AI 编程助手

### 4.2 安装模式
- **Copy**: 复制文件到目标目录（默认）
- **Symlink**: 创建符号链接到目标目录

---

## 5. 核心流程

### 5.1 需求分析流程
1. 需求收集 (adk-requirements-triage)
2. 架构设计 (adk-adr-writer)
3. 任务分解 (adk-task-breakdown)

### 5.2 开发流程
1. 接口设计 (adk-interface-contract-design)
2. 寄存器映射 (adk-register-map-design)
3. 驱动开发 (adk-driver-bringup-checklist)
4. BSP 移植 (adk-bsp-porting-playbook)

### 5.3 验证流程
1. 单元测试 (adk-unit-test-embedded)
2. 集成测试 (adk-integration-hil-sil)
3. 性能分析 (adk-performance-profiling-embedded)
4. 静态分析 (adk-static-analysis-c-cpp)

### 5.4 发布流程
1. 版本管理 (adk-release-versioning)
2. 提交门禁 (adk-commit-pr-quality-gate)
3. 文档审查 (adk-grill-with-docs)

---

## 6. 命名约定

### 6.1 文件命名
- **Agent 目录**: `agents/<kebab-case-name>/`
- **Skill 目录**: `skills/<kebab-case-name>/` 或 `optional-skills/<kebab-case-name>/`
- **脚本文件**: `scripts/<kebab-case-name>.sh`
- **文档文件**: `docs/<kebab-case-name>.md`

### 6.2 内部命名
- **Agent ID**: `<kebab-case-name>`
- **Skill ID**: `<kebab-case-name>`
- **Profile ID**: `<kebab-case-name>`

---

## 7. 依赖关系

### 7.1 Skill 依赖
- 依赖关系在 `manifest.yaml` 的 `depends_on` 字段中定义
- 依赖必须是有向无环图 (DAG)
- 安装时自动解析依赖链

### 7.2 Profile 依赖
- Profile 可以继承其他 Profile
- 继承关系在 `manifest.yaml` 的 `extends` 字段中定义
- 冲突关系在 `conflicts_with` 字段中定义

---

## 8. 验证要求

### 8.1 必须验证项
- 所有测试必须通过: `bash tests/run_all.sh`
- 健康检查必须通过: `bash scripts/health-check.sh check-all`
- 质量门禁必须通过: `bash scripts/quality-gate-check.sh check-all`

### 8.2 验证证据
- 每个验证步骤必须生成证据文件
- 证据文件位置: `docs/changes/<change-name>/verify-report.md`
- 证据必须包含: 命令、输出、结果、时间戳

---

## 9. 文档要求

### 9.1 必须文档
- **README.md**: 项目介绍和快速开始
- **CONTEXT.md**: 领域语言定义（本文件）
- **manifest.yaml**: 资产清单和配置
- **CHANGELOG.md**: 版本变更记录

### 9.2 Skill 文档
每个 SKILL.md 必须包含:
- **Frontmatter**: name, description, triggers, non_triggers, inputs, outputs, constraints
- **Body**: Goal, Prerequisites, Workflow, Quality Gate, Failure Handling

---

## 10. 版本管理

### 10.1 版本格式
- 使用语义化版本: `MAJOR.MINOR.PATCH`
- **MAJOR**: 不兼容的 API 修改
- **MINOR**: 向下兼容的功能性新增
- **PATCH**: 向下兼容的问题修正

### 10.2 版本来源
- **单一事实源**: `manifest.yaml` 中的 `version` 字段
- **其他文件**: 从 manifest.yaml 派生或同步

---

## 11. 安全要求

### 11.1 代码安全
- 禁止硬编码密钥和密码
- 使用环境变量或配置文件管理敏感信息
- 定期进行安全扫描

### 11.2 操作安全
- 破坏性操作必须有 `--force` 门控
- 删除操作前必须创建备份
- 重要操作必须有审计日志

---

## 12. 性能要求

### 12.1 响应时间
- 安装操作: <30 秒
- 验证操作: <10 秒
- 匹配操作: <1 秒

### 12.2 资源使用
- 内存使用: <100MB
- 磁盘空间: <50MB（不含依赖）

---

## 13. 监控要求

### 13.1 必须监控项
- 安装成功率
- 验证通过率
- 脚本执行时间
- 错误率

### 13.2 告警条件
- 安装失败率 >5%
- 验证失败率 >10%
- 脚本执行时间 >30 秒
- 错误率 >1%

---

## 14. 维护要求

### 14.1 定期维护
- 每周: 检查依赖更新
- 每月: 安全扫描
- 每季: 性能优化

### 14.2 文档更新
- 代码变更必须同步更新文档
- 新功能必须添加使用示例
- 废弃功能必须标记并提供迁移路径

---

## 15. 贡献指南

### 15.1 代码贡献
1. Fork 项目
2. 创建功能分支
3. 提交变更
4. 创建 Pull Request
5. 通过代码审查
6. 合并到主分支

### 15.2 文档贡献
1. 修复错误
2. 添加示例
3. 改进说明
4. 翻译内容

---

## 16. 许可证

- **许可证**: MIT License
- **Copyright**: 2026 agent-dev-kit contributors

---

## 17. 术语表

| 术语 | 定义 | 单一事实源 |
|------|------|------------|
| Agent | 面向固定职责的执行角色，负责分析、实现、验证或评审中的一个边界 | `agents/<name>/AGENTS.md` |
| Skill | 可复用能力单元，定义触发条件、输入输出、流程、命令和质量门禁 | `skills/<name>/SKILL.md` |
| Optional Skill | 默认不安装的扩展能力，只在 profile 或用户明确选择时启用 | `optional-skills/<name>/SKILL.md` |
| Profile | Agent 与 Skill 的可安装组合，面向具体工作场景 | `manifest.yaml` |
| Workflow | 从需求、设计、实现、验证到归档的阶段化执行链路 | `docs/workflows.md` |
| Artifact | 工作流阶段产物，如 proposal、design、tasks、verify-report、review-report | `templates/artifacts/` |
| Gate | 阶段入口或出口的质量检查，必须有命令或证据支撑 | `scripts/` 与 `tests/` |
| Evidence | 验证证据，记录命令、退出码、摘要和证据路径 | `docs/changes/<change>/` |

---

## 18. 概念关系

1. `manifest.yaml` 是 Agent、Skill、Optional Skill 与 Profile 的结构化索引。
2. Profile 选择一组 Agent 和 Skill；安装、转换和 Codex handoff 都从 Profile 解析资产。
3. Workflow 定义执行顺序；Skill 提供单步方法；Agent 承担角色职责。
4. Artifact 是 Workflow 的可审计输出；Gate 检查 Artifact 与 Evidence 是否满足进入下一阶段的条件。
5. `agent-dev-kit` 的生产链路是先生成符合 `~/codex` 规范的 handoff，再由 `~/codex` apply 到 `~/.codex`。

---

## 19. 使用规范

1. 新增或修改 Agent/Skill 必须同步 `manifest.yaml`，并运行 `rtk agent-dev-kit/scripts/devkit.sh validate --strict`。
2. 修改路由、触发词或 profile 时，必须运行 `rtk agent-dev-kit/tests/test_skill_trigger_matrix.sh` 与 `rtk agent-dev-kit/tests/test_match_effectiveness.sh`。
3. 修改 Codex 交接链路时，必须运行 `rtk agent-dev-kit/scripts/devkit.sh codex-handoff --codex-root "$HOME/codex"`。
4. 声明完成前必须运行与改动范围匹配的验证；无验证证据不得声明可发布、可安装或可合并。
5. 不直接把 `agent-dev-kit` 产物复制到 `~/.codex`；必须先进入 `~/codex` 源资产、manifest 和 apply plan 治理链路。

---

## 20. 联系方式

- **问题反馈**: GitHub Issues
- **功能建议**: GitHub Discussions
- **安全漏洞**: 安全邮箱

---

## 21. 致谢

感谢所有贡献者和用户的支持！

---

*本文档定义了 agent-dev-kit 的领域语言和核心概念，是理解项目的基础。*
