# Datasheet RAG 知识库

## 用途

存储 SoC datasheet 的结构化索引，支持 AI 快速检索寄存器定义、外设规格、时序参数等信息。

## 目录结构

```
datasheets/
├── README.md                    # 本文件
├── index.yaml                   # datasheet 索引
├── {soc-name}/                  # 按 SoC 分类
│   ├── metadata.yaml            # 元数据（厂商、型号、版本）
│   ├── registers/               # 寄存器定义
│   │   ├── {peripheral}.yaml    # 按外设分类
│   │   └── ...
│   ├── peripherals/             # 外设规格
│   │   ├── {peripheral}.md      # 外设描述
│   │   └── ...
│   └── errata/                  # 芯片勘误
│       └── errata.md
└── templates/
    ├── register-template.yaml   # 寄存器模板
    └── peripheral-template.md   # 外设模板
```

## 使用方式

### 1. 添加新 SoC 的 datasheet

```bash
# 创建 SoC 目录
mkdir -p datasheets/{soc-name}/{registers,peripherals,errata}

# 复制模板
cp templates/register-template.yaml datasheets/{soc-name}/registers/
cp templates/peripheral-template.md datasheets/{soc-name}/peripherals/
```

### 2. 查询寄存器信息

AI 可以通过以下方式查询：
- 直接读取 YAML 文件
- 使用 `grep` 搜索寄存器名称
- 使用索引文件快速定位

### 3. 引用规范

在代码中引用 datasheet 时，必须注明：
- SoC 型号
- datasheet 版本
- 页码或章节号

```c
/* 寄存器定义参考: i.MX8MP RM Rev.1, Page 1234 */
#define REG_CTRL  0x00
```

## 注意事项

1. **NDA 保护**: 涉及 NDA 的 datasheet 不得上传到公开仓库
2. **版本管理**: datasheet 更新时必须同步更新索引
3. **引用验证**: AI 生成的寄存器代码必须人工核对至少 3 处
