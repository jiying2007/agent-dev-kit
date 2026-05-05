---
name: static-analysis-c-cpp
description: C/C++ 静态分析与缺陷治理
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 质量门禁或疑难 bug 排查时
non_triggers:
  - 快速原型验证
inputs:
  - 代码路径、规则集
outputs:
  - 缺陷报告与修复建议
constraints:
  - 高优先级缺陷必须阻断合并
---

# static-analysis-c-cpp

## Goal
- 通过静态分析尽早发现高风险缺陷并闭环整改。

## Prerequisites
- 确认编译数据库或分析配置可用。
- 约定规则集严重级别映射（blocker/major/minor）。

## Workflow
1. 规则基线设定：按项目风险选择规则集。
2. 执行扫描：输出问题、位置、规则编号和严重级别。
3. 去噪与归因：剔除误报并保留依据。
4. 整改优先级：优先处理内存安全、并发、未定义行为问题。
5. 回归确认：修复后重跑扫描并比对残留问题。

## Commands
```bash
clang-tidy -p build compile_commands.json <file_or_dir>
cppcheck --enable=warning,style,performance --project=compile_commands.json
```

## Evidence Template
```md
- Rule Set:
- Scan Summary (B/M/m):
- Top Blockers:
- False Positive Notes:
- Re-scan Delta:
```

## Failure Handling
- 扫描无法执行时先修复编译数据库再继续。
- 误报争议需记录判定依据，不得直接忽略不留痕。

## Quality Gate
- blocker 必须清零或给出批准豁免记录。
- major 需有明确整改计划与 owner。
- 扫描结果必须可复跑并可比对。

---

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "这个告警是误报不用管" | 被忽略的"误报"往往是真实缺陷的遮羞布 | 按 SKILL.md 逐条确认并记录豁免理由 |
| "老代码一直这么写的" | 技术债不会因为存在时间长就变成正确做法 | blocker 必须清零，major 需有整改计划 |
| "静态分析太慢影响开发节奏" | 生产事故比分析慢 100 倍 | 将扫描集成到 CI，结果可复跑可比对 |
