# 芯片勘误库

## 用途

存储芯片勘误（errata）信息，支持 AI 识别已知问题和 workaround。

## 目录结构

```
errata/
├── README.md                    # 本文件
├── index.yaml                   # 勘误索引
├── {soc-name}/                  # 按 SoC 分类
│   ├── metadata.yaml            # 元数据（厂商、型号、版本）
│   ├── errata.md                # 勘误列表
│   └── workarounds/             # 解决方案
│       ├── {errata-id}.md       # 单个勘误的解决方案
│       └── ...
└── templates/
    ├── errata-template.md       # 勘误模板
    └── workaround-template.md   # 解决方案模板
```

## 勘误格式

每个勘误文件包含：

```markdown
# 勘误标题

## 基本信息
- 勘误 ID: xxx
- 芯片型号: xxx
- 影响版本: xxx
- 严重程度: 高/中/低

## 问题描述
[详细描述问题]

## 影响范围
[哪些功能/外设受影响]

## 触发条件
[什么情况下会触发]

## 解决方案
[官方推荐的 workaround]

## 参考资料
- [datasheet 页码]
- [官方 errata 文档链接]

## 贡献者
- [姓名] - [日期]
```

## 使用方式

### 1. 查询勘误

AI 可以通过以下方式查询：
- 按 SoC 分类查找
- 按严重程度分类查找
- 按影响范围分类查找

### 2. 添加新勘误

```bash
# 创建 SoC 目录
mkdir -p {soc-name}/workarounds

# 复制模板
cp templates/errata-template.md {soc-name}/errata.md
cp templates/workaround-template.md {soc-name}/workarounds/
```

### 3. 引用规范

在代码中引用勘误时，必须注明：
- 勘误 ID
- 芯片型号
- workaround 描述

```c
/* Workaround for errata ERR001234: xxx */
#define WORKAROUND_VALUE  0x1234
```

## 注意事项

1. **版本跟踪**: 芯片版本更新时必须同步更新勘误
2. **验证优先**: 使用 workaround 前必须验证有效性
3. **文档同步**: 勘误信息必须同步到代码注释
