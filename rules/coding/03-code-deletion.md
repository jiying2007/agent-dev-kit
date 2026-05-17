---
id: coding-003-code-deletion
title: 代码删除规则
languages: [all]
layers: [code]
stages: [build, review]
checks: [code-deletion-verified]
---

# 代码删除规则

> 来源: agent-dev-kit 代码治理基线

## 规则描述

AI 很容易认为"没人用"就想删代码，但动态 import、反射、mock 这些它看不到。必须有人工确认才能删除。

## 规则要求

### R8.1 删代码门槛

删除 ≥ 5 行代码或修改公共 API 前，必须：

1. **grep 全库**: 列出所有调用点
2. **分析依赖**: 检查是否有动态 import、反射、mock
3. **人工确认**: 用户说删才能删

### R8.2 实现方式

```bash
# 删除前检查
grep -r "function_name" . --include="*.c" --include="*.h" --include="*.py" --include="*.sh"
grep -r "symbol_name" . --include="*.c" --include="*.h"

# 检查动态引用
grep -r "import\|require\|dlopen\|dlsym" . --include="*.c" --include="*.py"
```

### R8.3 例外情况

以下情况可以自动删除：
- 明确标记为 `deprecated` 的代码
- 测试文件中的 mock 代码
- 临时文件和缓存文件

## 示例

### 正确示例

```
AI: 我想删除 utils.c 中的 helper_function()
AI: 先 grep 一下...
AI: 发现 3 个调用点: main.c:45, test.c:12, module.c:78
AI: 用户确认后才能删除
```

### 错误示例

```
AI: 这个函数没人用，我删了
AI: (直接删除，没有 grep 检查)
```

## 检查命令

```bash
# 检查是否有未确认的删除
git diff --stat | grep -E "^\s*\d+\s+deletion"
```

## 参考

- agent-dev-kit 代码治理基线 R8
- AGENTS.md R8 删代码门槛
