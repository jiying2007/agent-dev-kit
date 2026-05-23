# 贡献指南

## 概述

欢迎贡献到 agent-dev-kit！本指南帮助你了解如何为项目做出贡献。

## 贡献方式

### 1. 代码贡献
- 修复缺陷
- 添加新功能
- 改进性能
- 优化代码

### 2. 文档贡献
- 改进文档
- 添加示例
- 修复错误
- 翻译文档

### 3. 测试贡献
- 添加测试用例
- 改进测试覆盖
- 修复测试问题

### 4. 反馈贡献
- 报告问题
- 提出建议
- 分享经验
- 参与讨论

## 贡献流程

### 1. 准备工作
```bash
# 1. Fork项目
# 2. 克隆仓库
git clone https://github.com/your-username/agent-dev-kit.git
cd agent-dev-kit

# 3. 创建分支
git checkout -b feature/my-feature
```

### 2. 开发工作
```bash
# 1. 修改代码
# 2. 运行测试
bash tests/run_all.sh

# 3. 检查质量
bash scripts/quality-gate-check.sh check-all
```

### 3. 提交工作
```bash
# 1. 添加文件
git add .

# 2. 提交更改
git commit -m "feat: 添加新功能"

# 3. 推送分支
git push origin feature/my-feature
```

### 4. 创建Pull Request
- 访问GitHub
- 创建Pull Request
- 填写描述
- 等待评审

## 代码规范

### 1. 命名规范
- 文件名：小写字母，连字符分隔
- 变量名：小写字母，下划线分隔
- 函数名：小写字母，下划线分隔
- 常量名：大写字母，下划线分隔

### 2. 格式规范
- 缩进：2个空格
- 行宽：80字符
- 换行：LF
- 编码：UTF-8

### 3. 注释规范
- 文件头：说明文件用途
- 函数注释：说明功能、参数、返回值
- 代码注释：解释复杂逻辑
- 示例注释：提供使用示例

### 4. 提交规范
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- feat: 新功能
- fix: 修复缺陷
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试相关
- chore: 构建/工具

## 测试规范

### 1. 测试覆盖
- 关键路径：必须测试
- 边界条件：必须测试
- 错误路径：必须测试
- 性能测试：可选

### 2. 测试命名
```bash
# 测试文件
test_<module>.sh

# 测试函数
test_<function>_<scenario>
```

### 3. 测试结构
```bash
#!/usr/bin/env bash
set -euo pipefail

# 测试函数
test_my_function() {
    # 准备
    local input="test"
    
    # 执行
    local result
    result=$(my_function "$input")
    
    # 验证
    assert_equal "$result" "expected"
}

# 运行测试
run_tests() {
    test_my_function
}

# 主函数
main() {
    run_tests
}

main "$@"
```

## 文档规范

### 1. 文档结构
- 标题：清晰明确
- 概述：简要说明
- 正文：详细内容
- 示例：使用示例
- 参考：相关链接

### 2. 文档格式
- Markdown格式
- 代码块：带语言标识
- 链接：使用相对路径
- 图片：使用相对路径

### 3. 文档维护
- 定期更新
- 修复错误
- 添加示例
- 改进说明

## 问题报告

### 1. 问题描述
- 清晰明确
- 提供上下文
- 包含错误信息
- 提供重现步骤

### 2. 环境信息
- 操作系统
- Bash版本
- Git版本
- 相关工具版本

### 3. 重现步骤
```bash
# 1. 执行命令
bash scripts/health-check.sh check-all

# 2. 观察结果
[ERROR] 健康检查失败

# 3. 期望结果
[SUCCESS] 所有健康检查通过
```

## 功能建议

### 1. 建议描述
- 清晰明确
- 提供背景
- 说明需求
- 提供示例

### 2. 需求分析
- 问题描述
- 解决方案
- 影响范围
- 优先级

### 3. 实现建议
- 技术方案
- 实现步骤
- 测试计划
- 文档更新

## 评审流程

### 1. 评审标准
- 代码质量
- 测试覆盖
- 文档完整性
- 性能影响

### 2. 评审步骤
```bash
# 1. 检查代码
bash scripts/quality-gate-check.sh check-all

# 2. 运行测试
bash tests/run_all.sh

# 3. 检查文档
bash scripts/health-check.sh check-structure

# 4. 检查质量
bash scripts/health-check.sh check-quality
```

### 3. 评审反馈
- 具体明确
- 提供建议
- 尊重他人
- 保持专业

## 发布流程

### 1. 版本规划
- 功能规划
- 时间规划
- 资源规划
- 风险规划

### 2. 发布准备
```bash
# 1. 运行测试
bash tests/run_all.sh

# 2. 检查质量
bash scripts/quality-gate-check.sh check-all

# 3. 创建备份
bash scripts/backup-rollback.sh backup --target ~/codex

# 4. 升级到下一目标版本
bash scripts/version-manager.sh upgrade --target 3.0.0
```

### 3. 发布执行
```bash
# 1. 锁定当前稳定版本
bash scripts/version-manager.sh lock --version 2.9.0

# 2. 生成变更日志
bash scripts/version-manager.sh changelog

# 3. 创建发布报告
# 4. 发布版本
```

## 社区规范

### 1. 行为准则
- 尊重他人
- 保持专业
- 积极参与
- 建设性反馈

### 2. 沟通规范
- 清晰明确
- 尊重他人
- 保持专业
- 积极参与

### 3. 冲突解决
- 理解对方
- 寻求共识
- 尊重决定
- 保持专业

## 获取帮助

### 1. 文档资源
- 使用指南：`docs/usage.md`
- 命令参考：`docs/commands.md`
- 故障排除：`docs/troubleshooting.md`
- 最佳实践：`docs/best-practices.md`

### 2. 社区资源
- GitHub Issues
- 讨论区
- 邮件列表
- 文档

### 3. 联系方式
- 维护团队
- 社区讨论
- 邮件联系

## 贡献者列表

感谢所有贡献者的付出！

---

**提示**：贡献是开源项目的生命线，感谢你的参与！
