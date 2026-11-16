# 任务与当前状态

前置设计：@docs/changes/20261116-skill-practical-methods/design.md。

| ID | 独占写集/责任 | 状态 | 验证 |
|---|---|---|---|
| T1 | root/独立研究：来源、合同、原始反例归档 | 研究及独立设计预审完成 | 固定作者文件/官方文档，真实反例与能力缺口，不声称穷尽全网 |
| T2 | general：code-review-loop 主入口/对应 evidence reference；context-engineering/context-compress-handoff；test_skill_content_contract.py | 实现完成；独立定向复核通过 | 4 Git 状态、stat-only index 保持；该阶段 27 项通过；随后 SOP 字段恢复由 green-sop / green-t2 和最新完整回执闭合 |
| T3 | practical：ADC src/header/native test、必要 example README/CMakeLists.txt/cross-build/smoke-command.txt；test_skill_command_examples.py | native 与源码接线完成；CMake 实跑待平台 | 原 3 测试阳性；14 边界向量、真实 native/UBSan；独立 C11 实现/C90 消费者编译链接通过 |
| T4 | practical：performance-profiling-embedded、cmake-cross-build；CMake 实测也归 test_skill_command_examples.py | 实现完成；5 个 CMake case 留待平台验证 | 本地 21 PASS / 5 明确 skip；GitHub Actions 缺工具必须失败，不能凭本地组通过验收实跑 |
| T5 | root：optional test-flakiness-triage 主入口与已有 reference | 实现及独立早审完成 | 原始同进程/独跑/反序证据，条件性方法与部署可见性；不新增无效测试计数 |
| T6 | root：protocol-stack-integration 主入口 | 实现及独立早审完成 | 阶段/退避占预算与嵌套重试方法反例、错误语义/时钟/长连接边界 |
| T7 | root：版本 11.3.6、fixture、catalog、预算、完整验证；独立审核只读 | 本地全部完成；独立最终裁决由 review-evidence.json 给出 | 最新 9a918fa：102/102 组通过、30 源码摘要不变、8 原 ratchet 全通过；局部工具缺失如实记录 |
| T8 | root：#270 闭环与本轮 PR/main/Release | 11.3.5 合并/main CI/正式 Release 均完成；11.3.6 留待平台资格 | 原始平台回执见 prior-publication.json；11.3.6 必须经最终 HEAD CI（含真实 CMake）、正常 merge、main CI 和自动发布 |

执行约束：本环境 rtk 缺失的实际异常沿用上轮证据，直接调用原工具；无外部模型或定时任务。独立 external 设计预审 Spec/Quality pass、无 blocker/major，报告与计划原始摘要保留。root 完成 T5/T6 后承担集成；general/practical 源码停写，external 保持独立只读审查。#270 合并提交 `008c789312ed374f38d6d71a113f8fc91f89e63c` 的 main CI 与正式 Release 已按真实回执闭合。

集成修订：root 完成 T5/T6 后转集成；独立 reviewer 与 practical 均核实新 `_Static_assert` 的 C11 前置条件须在既有 ADC 构建入口显式声明。T3 写集据此增加现有 CMakeLists 和 cross smoke 两路径，无 API/功能或门禁扩大；实现选择 PRIVATE 编译特性，header/test 没有 C11 专属语法。原始预审摘要保持，不冒充它已覆盖后来修订。

封装截点：本页记录最终源码冻结与已取得的本地证据；随后平台 CI、合并和 Release 状态由对应 PR/Actions/Release 的真实对象给出，不通过修改冻结结果倒填。当前源码 `9a918fa33e02313681649a52713d04750ef0bf0b`，最多三个后续动作：独立源码裁决与证据封装、最终 PR CI 核 CMake、正常合并并核自动发布。
