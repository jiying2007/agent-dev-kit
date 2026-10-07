# 阶段计划

- [x] 基线：根仓及 ADK 状态核验，用户 dirty 保护，Provider 显式项目路由成功，新目标登记。
- [x] 审查：重复键末值覆盖实验与外部一手资料。
- [x] 实施：三个读入口及晋级原子输出；真实目标路径保留叶节点，native 摘要与解码同字节。
- [x] 定向与复审：14 项定向通过；首次两个 Major 修复，working-tree 整批复审 spec/quality PASS。
- 全量/交付验收：冻结 index 后运行三 Python full parity；仅实际终态 receipt 支持通过。随后执行 staged 复审、SCM 与 consumer 精确身份读回；结果进本轮根仓交付记录及 Provider reviewing，不预填成功。

工作项：implementation；owner 主 Agent；权限为当前源码修复及已有交付授权。验证共享源和 build 串行，readonly 独立复审不运行写测试。
retry_budget=2；staleness_threshold=60分钟；连续两次同类失败更新假设，stop_condition=pass/replan/blocked；新 Major 类出现两轮触发 replan。
required_evidence=audit,research,tests,review；验收不能由旧测试/旧签名替代。恢复保留当前分支、修改清单、命令结果和最多三个下一步。
本轮最终运行回执：/tmp/adk-803-staged-evidence-json-parity-20261007.json；对应 actual source/index 由 receipt 字段和 check-receipt 核验。源码文档只定义验收，不承载尚未发生的成功声明。
