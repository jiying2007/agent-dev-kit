# 发布来源与合同一致性修复

## 目标与授权

用户 2026-10-23 要求“全面吸收，全面优化，落地闭环”，关闭 ADK-01、ADK-02、ADK-03。基线 bf9ec8164e2c80394ce997f8a8b51515cad4746e。既有自动推进/审核及组件发布授权有效；不授予任何产品资格。

## 验收

1. 可发布的 git-clean-commit 产物从固定 Git tree 的受跟踪 blob 快照编译和打包；ignored 残留不得进入，工作树隐藏内容漂移不得改变该产物。
2. 保留显式发布 surface、文件模式、现有开发构建不可发布的语义；快照读取失败应明确拒绝。
3. canonical artifact verifier 有界重算 source 成员、数量、规范摘要，核对嵌入 source manifest；拒绝重复、异常类型和非法路径。
4. 公开 publish 与 canonical validator 对版本、tar/sha256/release-contract 完整资产集合使用相同规则；dry-run 同样拒绝改名和内部漂移。
5. 正常干净发布仍可确定性重建；签名、来源证明、组件发布、runtime 和产品资格继续独立。
6. 回归不得真实发布 fixture，不执行付费模型评测。

## 非目标

不改信任根、不放宽 CI、签名或产品要求，不用内部摘要替代签名验证，不增加外部构建平台。
