# Oops 模式库

## 用途

存储 kernel oops/panic 的常见模式和解决方案，支持 AI 快速定位硬件交互问题。

## 目录结构

```
oops-patterns/
├── README.md                    # 本文件
├── index.yaml                   # 模式索引
├── categories/                  # 按错误类型分类
│   ├── null-pointer.md          # 空指针解引用
│   ├── page-fault.md            # 页错误
│   ├── deadlock.md              # 死锁
│   ├── use-after-free.md        # 释放后使用
│   ├── stack-overflow.md        # 栈溢出
│   └── ...
├── drivers/                     # 按驱动分类
│   ├── mmc/
│   ├── usb/
│   ├── i2c/
│   ├── spi/
│   └── ...
└── templates/
    └── pattern-template.md      # 模式模板
```

## 模式格式

每个模式文件包含：

```markdown
# 模式名称

## 错误信息
[完整的 oops/panic 信息]

## 错误类型
[空指针/页错误/死锁/...]

## 可能原因
1. 原因 1
2. 原因 2

## 排查方向
1. 检查 xxx
2. 查看 yyy

## 解决方案
[具体的修复方法]

## 参考资料
- [链接 1]
- [链接 2]

## 贡献者
- [姓名] - [日期]
```

## 使用方式

### 1. 查询模式

AI 可以通过以下方式查询：
- 按错误类型分类查找
- 按驱动分类查找
- 使用关键词搜索

### 2. 添加新模式

```bash
# 创建新模式
cp templates/pattern-template.md categories/{error-type}/{new-pattern}.md

# 编辑模式内容
vim categories/{error-type}/{new-pattern}.md
```

### 3. 引用规范

在分析 oops 时，必须引用：
- 模式名称
- 模式文件路径
- 置信度（高/中/低）

```markdown
根据 oops 模式库中的 "null-pointer-in-mmc-probe" 模式，
该问题可能是由于 mmc 控制器初始化失败导致的。
置信度: 中
```

## 注意事项

1. **模式验证**: 新添加的模式必须经过至少 3 次实际验证
2. **版本更新**: 内核版本更新时必须同步更新模式
3. **置信度标注**: 所有模式必须标注置信度
