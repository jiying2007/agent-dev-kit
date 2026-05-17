---
name: adk-code-simplification
description: 代码简化——在不改变行为的前提下提高清晰度
version: 1.1.0
last_updated: 2026-05-06
triggers:
  - "代码太复杂"
  - "简化代码"
  - "重构这段代码"
non_triggers:
  - "添加新功能"
  - "修复 bug"
inputs:
  - 待简化代码
outputs:
  - 简化后代码
constraints:
  - 不改变行为
  - 必须有测试覆盖
---

# 代码简化

## Goal
- 在不改变行为的前提下提高代码清晰度和可维护性。


## Prerequisites
- 确认待简化代码有测试覆盖。
- 获取最小上下文：代码路径、测试命令。


## Workflow
1. **确认测试覆盖**：确保有测试保护现有行为。
   ```bash
   # 运行现有测试
   <test-cmd> --filter <target_module>
   ```
2. **识别代码异味**：按异味表逐项扫描目标代码。
   ```bash
   # 查找长函数
   rg -n "^(void|int|static|public|private).*\(" <file> | head -20
   # 查找深层嵌套
   rg -n "^\s{12,}" <file>  # 3 层以上缩进
   # 查找重复代码
   rg -c "pattern" <files>  # 高频出现的模式
   ```
3. **选择简化模式**：按核心原则选择合适模式。
4. **执行简化**：一次一个模式，每步后运行测试。
5. **对比验证**：确认行为不变、可读性提升。
   ```bash
   # 运行测试确认行为不变
   <test-cmd> --filter <target_module>
   # 对比行数
   wc -l <file_before> <file_after>
   ```


## Quality Gate
- 简化前后测试全部通过。
- 代码行数减少或可读性提升。
- 无行为变更。
- 单次简化只应用一种模式。
- 简化后圈复杂度不高于简化前。


## Failure Handling
- 简化后测试失败则立即回滚，分析失败原因。
- 若无法确定某行代码是否有用，先不删除，标记 TODO。
- 简化导致性能下降时，回滚并评估 trade-off。
- 若代码异味根因是架构问题，记录到 ADR 而非强行简化。


## Evidence Template

```md
status: pass | needs-fix | BLOCKED
commands:
- <command + exit code>
evidence:
- <path or output summary>
risks:
- <remaining risk or none>
```

## References
- 详细背景、命令、模板、示例和扩展检查项保存在 `references/details.md`。
- 入口文件只保留触发和执行所需的最小上下文，避免默认加载过多 token。
