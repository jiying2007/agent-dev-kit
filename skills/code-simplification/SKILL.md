---
name: code-simplification
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

## 核心原则

1. **Chesterton's Fence**: 简化前先理解为什么要这样写
2. **Rule of 500**: 500 行内可理解的简化优先
3. **DRY 但不过度**: 重复 3 次以上才抽象
4. **可读性优先**: 清晰 > 简短
5. **测试先行**: 简化前确保有测试覆盖

## 代码异味识别

| 异味 | 表现 | 简化模式 |
|------|------|---------|
| 长函数 | >50 行，多层嵌套 | 提取函数 |
| 深层嵌套 | if/for 嵌套 >3 层 | 卫语句/早期返回 |
| 复杂条件 | 条件表达式 >3 个子句 | 表驱动/策略模式 |
| 重复代码 | 相同逻辑出现 3+ 次 | 提取公共函数 |
| 死代码 | 未使用的变量/函数/分支 | 直接删除 |
| 魔法数字 | 硬编码数字无说明 | 提取常量 |
| 过长参数 | 函数参数 >4 个 | 参数对象/Builder 模式 |
| 数据泥团 | 总是一起出现的参数 | 提取结构体/类 |

## 简化前后对比

### 提取函数
```c
// Before: 40 行处理函数
void process(data_t *d) {
    // 10 行校验...
    // 15 行转换...
    // 15 行输出...
}

// After: 3 个清晰步骤
void process(data_t *d) {
    if (!validate(d)) return;
    transform(d);
    output(d);
}
```

### 卫语句消除嵌套
```c
// Before: 3 层嵌套
if (a) {
    if (b) {
        if (c) { do_something(); }
    }
}

// After: 早期返回
if (!a) return;
if (!b) return;
if (!c) return;
do_something();
```

### 表驱动替代复杂条件
```c
// Before: 长串 if-else
if (type == A) handle_a();
else if (type == B) handle_b();
else if (type == C) handle_c();

// After: 表驱动
handler_t handlers[] = {{A, handle_a}, {B, handle_b}, {C, handle_c}};
for (int i = 0; i < ARRAY_SIZE(handlers); i++) {
    if (handlers[i].type == type) { handlers[i].fn(); break; }
}
```

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

## Commands
```bash
# 运行测试
<test-cmd> --filter <target_module>

# 统计代码行数
wc -l <target_files>

# 查找复杂函数
awk '/^[a-zA-Z].*\(.*\)/{name=$0; count=0} /{/{count++} /}/ && count>0{count--; if(count==0 && NR-start>50) print NR": "name}' <file>

# 查找未使用代码
rg -n "unused|UNUSED|TODO.*remove|deprecated" <target_path>
```

## Evidence Template
```md
- 简化模式: <pattern>
- 代码异味: <smell type>
- 简化前:
  - 行数: N
  - 圈复杂度: X
  - 嵌套深度: D
- 简化后:
  - 行数: M
  - 圈复杂度: Y
  - 嵌套深度: E
- 测试结果: pass / needs-fix
- 行数变化: before N -> after M (Δ -K)
- 可读性评估: 提升/持平
```

## Failure Handling
- 简化后测试失败则立即回滚，分析失败原因。
- 若无法确定某行代码是否有用，先不删除，标记 TODO。
- 简化导致性能下降时，回滚并评估 trade-off。
- 若代码异味根因是架构问题，记录到 ADR 而非强行简化。

## Quality Gate
- 简化前后测试全部通过。
- 代码行数减少或可读性提升。
- 无行为变更。
- 单次简化只应用一种模式。
- 简化后圈复杂度不高于简化前。

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "原作者有原因才这么写" | 可能是历史遗留 | 先理解再决定是否简化 |
| "简化可能引入 bug" | 有测试就不怕 | 确保测试覆盖再简化 |
| "这段代码以后会改" | "以后"永远不会来 | 现在简化，减少未来债务 |

## 健壮性规范

- **输入验证**: 确认代码有测试覆盖
- **重试策略**: 简化后测试失败则回滚
- **超时控制**: 单次简化不超过 30 分钟
- **异常隔离**: 一次只简化一个模式
- **日志记录**: 记录简化前后的对比
