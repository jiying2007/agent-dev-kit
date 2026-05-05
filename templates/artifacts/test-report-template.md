# Test Report (测试报告)

[artifact:test-report]
status: DRAFT
owner: [填写负责人]
scope:
- [本次测试覆盖的模块/功能]
inputs:
- [测试计划、需求文档、代码变更列表]
handoff_to:
- reviewer, release-manager

> **使用场景**: 在 verify 阶段输出测试执行结果，证明变更符合预期且未引入回归问题。
> **适用角色**: tester, backend-developer, firmware-developer

---

## 1. Test Scope (测试范围)

- **测试对象**: [被测模块/功能/服务名称]
- **测试类型**:
  - [ ] 单元测试 (Unit Test)
  - [ ] 集成测试 (Integration Test)
  - [ ] 端到端测试 (E2E Test)
  - [ ] 性能测试 (Performance Test)
  - [ ] 安全测试 (Security Test)
  - [ ] HIL/SIL 测试 (嵌入式场景)
- **测试版本/提交**: [Git commit hash 或版本号]
- **关联变更**: [本次测试对应的变更请求/PR 链接]

## 2. Test Environment (测试环境)

| 项目 | 配置 |
|------|------|
| OS | [操作系统及版本] |
| Runtime | [语言运行时版本, e.g., Python 3.11] |
| Hardware | [硬件平台, e.g., STM32F407 / x86_64] |
| Dependencies | [关键依赖及版本] |
| Test Framework | [测试框架, e.g., pytest / Unity / Google Test] |
| CI/CD | [CI 平台及 Job 链接] |

## 3. Test Cases Summary (测试用例汇总)

| 指标 | 数值 |
|------|------|
| 总用例数 | [N] |
| 通过 (Pass) | [N] |
| 失败 (Fail) | [N] |
| 跳过 (Skip) | [N] |
| 错误 (Error) | [N] |
| **通过率** | **[N%]** |
| 执行时间 | [总时长] |

## 4. Pass/Fail Details (通过/失败详情)

### 4.1 Failed Cases (失败用例)

| 用例ID | 用例名称 | 失败原因 | 严重程度 | 根因分析 | 状态 |
|--------|----------|----------|----------|----------|------|
| [TC-001] | [名称] | [原因] | [Critical/Major/Minor] | [根因] | [Open/Fixed/Won't Fix] |

### 4.2 Skipped Cases (跳过用例)

| 用例ID | 用例名称 | 跳过原因 |
|--------|----------|----------|
| [TC-002] | [名称] | [原因] |

### 4.3 Key Passed Cases (关键通过用例)

| 用例ID | 用例名称 | 场景描述 |
|--------|----------|----------|
| [TC-003] | [名称] | [描述] |

## 5. Coverage Metrics (覆盖率指标)

| 覆盖率维度 | 目标 | 实际 | 是否达标 |
|-----------|------|------|----------|
| 代码行覆盖率 (Line Coverage) | [≥80%] | [N%] | [Yes/No] |
| 分支覆盖率 (Branch Coverage) | [≥70%] | [N%] | [Yes/No] |
| 函数覆盖率 (Function Coverage) | [≥90%] | [N%] | [Yes/No] |
| 需求覆盖率 (Requirement Coverage) | [100%] | [N%] | [Yes/No] |

- **未覆盖区域**: [列出未覆盖的模块/函数及原因]
- **覆盖率报告链接**: [HTML 报告路径或 CI 链接]

## 6. Known Issues (已知问题)

| Issue ID | 描述 | 严重程度 | 影响范围 | 规避方案 | 跟踪状态 |
|----------|------|----------|----------|----------|----------|
| [ISSUE-001] | [描述] | [Critical/Major/Minor] | [范围] | [方案] | [Open/In Progress] |

## 7. Recommendations (建议与结论)

- **是否可发布/合入**: [Yes / No / Conditional]
- **条件** (如适用): [列出需要满足的前置条件]
- **改进建议**:
  1. [建议1: 例如"增加边界条件测试用例"]
  2. [建议2: 例如"优化测试环境隔离"]
  3. [建议3]
- **遗留风险**: [如有未修复的已知问题，说明风险评估]

---

## Checklist (完成清单)

- [ ] 测试范围明确，覆盖所有变更模块
- [ ] 测试环境已记录，可复现
- [ ] 所有用例执行结果已记录
- [ ] 失败用例有根因分析和状态跟踪
- [ ] 覆盖率指标已量化且达标（或已记录豁免原因）
- [ ] 已知问题已列出并有跟踪
- [ ] 结论和建议已给出
- [ ] 测试报告已通过评审 (review-passed)
