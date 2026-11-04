# adk-code-simplification — 补充参考资料

此参考文件只提供可选背景、示例和检查提示；当前能力流程、权限、回退与放行结论以 `../SKILL.md`、Manifest 及运行时门禁为准。示例命令不得被解释为写权限授权。

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
