# BSP 历史库

## 用途

存储 BSP（Board Support Package）的历史变更、patch 分析和架构演进，支持 AI 理解代码背景和设计决策。

## 目录结构

```
bsp-history/
├── README.md                    # 本文件
├── index.yaml                   # BSP 索引
├── {board-name}/                # 按开发板分类
│   ├── metadata.yaml            # 元数据（厂商、芯片、内核版本）
│   ├── architecture.md          # 架构说明
│   ├── patches/                 # patch 分析
│   │   ├── {patch-id}.md        # 单个 patch 分析
│   │   └── ...
│   ├── decisions/               # 设计决策记录
│   │   ├── {decision-id}.md     # 单个决策
│   │   └── ...
│   └── lessons/                 # 经验教训
│       └── lessons.md
└── templates/
    ├── patch-template.md        # patch 分析模板
    ├── decision-template.md     # 决策记录模板
    └── architecture-template.md # 架构说明模板
```

## Patch 分析格式

每个 patch 分析文件包含：

```markdown
# Patch 标题

## 基本信息
- Patch ID: xxx
- 作者: xxx
- 日期: xxx
- 内核版本: xxx

## 问题描述
[这个 patch 解决什么问题]

## 修改内容
[具体修改了哪些文件、哪些函数]

## 设计决策
[为什么选择这种方案]

## 风险评估
[可能引入的风险]

## 验证方法
[如何验证这个 patch]

## 相关 Patch
- [patch-id-1]
- [patch-id-2]

## 贡献者
- [姓名] - [日期]
```

## 使用方式

### 1. 查询 BSP 信息

AI 可以通过以下方式查询：
- 按开发板分类查找
- 按芯片分类查找
- 按内核版本分类查找

### 2. 添加新 BSP

```bash
# 创建 BSP 目录
mkdir -p {board-name}/{patches,decisions,lessons}

# 复制模板
cp templates/architecture-template.md {board-name}/architecture.md
cp templates/patch-template.md {board-name}/patches/
cp templates/decision-template.md {board-name}/decisions/
```

### 3. 分析 Patch

```bash
# 分析单个 patch
# 1. 读取 patch 内容
# 2. 填写 patch 分析模板
# 3. 评估风险和验证方法
```

## 注意事项

1. **NDA 保护**: 涉及 NDA 的 BSP 信息不得上传到公开仓库
2. **版本管理**: BSP 更新时必须同步更新历史库
3. **决策追溯**: 所有设计决策必须有记录和原因
