# Skill 格式指南

## SKILL.md 规范

SKILL.md 是 skill 的入口文件，应保持精简（建议 <150 行）。

### 必需章节
1. YAML frontmatter (name, description, triggers, non_triggers)
2. 核心流程（步骤化）
3. 输出契约

### 可选章节
- 合理化借口拦截
- 健壮性规范
- 示例

## references/ 子目录

当 SKILL.md 超过 150 行时，将详细参考资料拆分到 references/ 子目录：

```
skills/<skill-name>/
├── SKILL.md           # 精简入口（触发条件 + 核心流程）
└── references/
    ├── patterns.md    # 详细模式库
    ├── checklist.md   # 检查清单
    └── examples.md    # 示例代码
```

### 原则
- SKILL.md = Agent 需要立即知道的信息
- references/ = Agent 按需查阅的详细信息
- 减少 token 消耗，提高上下文效率
