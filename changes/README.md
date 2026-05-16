# 变更管理

## 用途

标准化管理每个需求从分析到交付的全过程，确保可追溯性和质量门禁。

## 目录结构

```
changes/
├── README.md                    # 本文件
├── templates/                   # 变更模板
│   ├── summary-template.md      # 全流程追溯摘要
│   ├── spec-template.md         # 需求分析文档
│   ├── tasks-template.md        # 任务拆分清单
│   ├── coding-report-template.md # 编码报告
│   ├── review-template.md       # 评审报告
│   └── test-report-template.md  # 测试报告
├── examples/                    # 变更示例
│   └── add-modbus-tcp/
│       ├── summary.md
│       ├── request_analysis/
│       │   ├── spec.md
│       │   └── tasks.md
│       ├── coding/
│       │   ├── coding_report_v1.md
│       │   └── review/
│       │       └── code_review_v1.md
│       ├── unit_test/
│       ├── ci_result/
│       └── deployment/
└── {变更类型}-{需求名称}-{YYYYMMDD}/  # 实际变更目录
```

## 变更类型

- `feature`: 新功能
- `fix`: 缺陷修复
- `refactor`: 重构
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 其他

## 使用方式

### 1. 创建新变更

```bash
# 创建变更目录
CHANGE_DIR="changes/feature-add-modbus-tcp-$(date +%Y%m%d)"
mkdir -p "$CHANGE_DIR"/{request_analysis,coding/review,unit_test,ci_result,deployment}

# 复制模板
cp templates/spec-template.md "$CHANGE_DIR/request_analysis/spec.md"
cp templates/tasks-template.md "$CHANGE_DIR/request_analysis/tasks.md"
cp templates/summary-template.md "$CHANGE_DIR/summary.md"
```

### 2. 填写变更文档

按照模板填写：
1. 需求分析文档 (spec.md)
2. 任务拆分清单 (tasks.md)
3. 全流程追溯摘要 (summary.md)

### 3. 执行变更流程

```bash
# 提议阶段
bash scripts/workflow.sh propose --change "$CHANGE_DIR"

# 实施阶段
bash scripts/workflow.sh apply --change "$CHANGE_DIR"

# 验证阶段
bash scripts/workflow.sh verify --change "$CHANGE_DIR"

# 评审阶段
bash scripts/workflow.sh review --change "$CHANGE_DIR"

# 归档阶段
bash scripts/workflow.sh archive --change "$CHANGE_DIR"
```

### 4. 质量门禁检查

```bash
# 运行通用质量门禁
bash scripts/quality-gates.sh "$CHANGE_DIR"

# 运行嵌入式专用门禁（如果是嵌入式代码）
bash scripts/quality-gates-embedded.sh "$CHANGE_DIR/coding/file.c"
```

## 变更状态

- `proposed`: 已提议
- `applied`: 已实施
- `verified`: 已验证
- `review-passed`: 评审通过
- `archived`: 已归档

## 注意事项

1. **一个变更一个问题**: 避免混合多个无关任务
2. **版本递增**: 评审报告采用版本递增策略（v1, v2, v3...）
3. **旧版本保留**: 旧版本永远不删，确保完整的审计链
4. **门禁强制**: 必须通过质量门禁才能进入下一阶段
