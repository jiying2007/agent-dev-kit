# 变更提案：20261117-task-diagnostics

## 背景
用户要求完成 LoopForge 与同类方案审查后的优化。Root 固定来源与独立 owner 决策记录在 docs/changes/20261117-loopforge-adoption；只吸收适合 ADK 的最小增量，第三方源码不进入产品。原 reports 路径的收集与 CI 失败保留为该包的历史证据。

## 问题陈述（单问题）
既有 task/trace 事实已验证，但缺少一个明确按需、不会制造测量结论的诊断视图。接口勘察确认无需另建 schema 或 runtime。

## 目标
在既有 eval import-task 提供可选 --diagnostics，保留原始失败、缺测与证据引用，并供既有 AAR 按需使用。

## 非目标
不新增调度器、Goal、MCP、默认诊断、外部价格估算或模型调用，不宣称 native/runtime/Token 改善已经测量。

## 上下文充分性检查
- [x] 已明确输入/输出与接口契约：requirements.md。
- [x] 已识别兼容、隐私、输入输出别名及模块大小风险。
- [x] 已明确验证命令与通过标准：tasks.md。
- [x] 宿主缺失已记录，源码工作不依赖宿主测量。

## Core/Optional 边界检查
- [x] 属于通用核心能力（core）
- 归属结论：现有 typed core 的可选事实视图及既有 AAR reference，无新资产。

## 变更重复性检查
已检索 trace_summary、task_evidence、evaluation_cli、repository_evaluation 和 AAR。既有过程认证字段不由调用次数推断；本次只增加 task import 按需投影。

## Breaking Change 检查
- [x] 否：默认 false，旧报告/返回码/资格与数据格式保持。新增兼容 CLI 功能按 SemVer 发布 11.4.0。

## Spec 链路检查
requirements.md 冻结反例；design.md 冻结边界；tasks.md 标明独立实现、审查和可执行 verify。

## Canonical Change Contract

| Requirement ID | Requirement | Operation | Target | Affected Surface | Acceptance ID | Acceptance Criterion | Task ID | Verification ID | Evidence Target |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | 显式按需诊断 | ADDED | eval import-task | CLI/import report | ACC-001 | 无 flag 原行为，失败导入和无效输入语义保持 | TASK-001 | VERIFY-001 | verify-report.md |
| REQ-002 | 事实与缺测无损投影 | ADDED | trace_summary.py | diagnostics | ACC-002 | 保留全部失败与 unavailable，不推断浪费或节省 | TASK-001 | VERIFY-002 | verify-report.md |
| REQ-003 | 复用既有核验边界 | MODIFIED | task_evidence.py | verified ledger | ACC-003 | 稳定纯投影、无额外读取、别名保护不变 | TASK-001 | VERIFY-003 | verify-report.md |
| REQ-004 | 按需复盘引用 | MODIFIED | adk-after-action-review | existing references | ACC-004 | 有命令、来源和限制，方法静态验证通过 | TASK-002 | VERIFY-004 | verify-report.md |
| REQ-005 | 受保护源码交付 | MODIFIED | release metadata | 11.4.0 | ACC-005 | 完整回归与独立审查，CI/release 当前提交核验 | TASK-003 | VERIFY-005 | verify-report.md |

## 安装范围与依赖边界
global-ready 的现有 ADK 资产，调用仅访问明确提供的任务包。不增加依赖和运行态安装；Root 只晋级源码 gitlink。

## Prompt 回归证据计划
同一 AAR 请求的 before/after 静态差异绑定 Git diff；保留既有 Skill method fixture。没有模型运行，效果为 not-measured；不得将静态验证升级成效果认证。

## 收敛模式与退出条件
execution。验收反例、完整回归、独立审核与当前发布证据齐备后收敛；宿主和效果缺测作为明确边界。

## 备选方案与取舍
选择现有 trace/task 导入的纯投影；不选新分析平台或扩展 repository certify，因为已有接口足以容纳事实且认证保持独立。

## 风险与回退
可选字段需保持默认兼容，计数不能形成推断标签，敏感原文不得回显。发现回归以受保护 revert 回滚，并将 Root 恢复到已核验 11.3.15 gitlink；历史证据保留。
