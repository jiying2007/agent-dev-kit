# 设计

基线为 `b20df018ca62436dd026daed6ec6944d4a45cbbd`（v11.3.10）。已有供应链 Skill 具备 source-to-sink 和范围门，但没有说明生成序列化的字段保护差异。采用方法级补充，保留原责任边界。

## 变更边界

1. 主入口只用现有敏感信息步骤的等行替换提示条件与参考文件，版本按 patch 前移；不扩大原 140 行上限。
2. 在现有 `references/skill-scan-coverage.md` 内增加精简检查步骤及 Python 标准库示例。检查源头、holder、serializer 和 sink，不以关键词/单处 repr 的成功代替通路证明。
3. 使用显式允许的非敏感字段生成遥测/响应对象；生产修复仍由具体合同决定，示例不是可覆盖所有类型的脱敏库。
4. 通过现有 Skill 内容测试入口执行发布示例，覆盖嵌套值、正常控制与无泄漏报告；按实际需要补 export 读取检查。只添加能发现示例错误/丢失引用的测试。
5. 复用原版本同步、回归、审核、发布与 Root source-only 事务；共享 manifest/版本/证据由集成者串行更新。

## 来源、风险与回滚

Sentry `secret-serialization` 的原始 Skill 与语言参考提供 holder/serializer/sink 思路；Python 官方 dataclasses 文档用于核验 repr/asdict 语义。固定来源与许可记录在本变更的审查记录中，仅吸收方法，中文说明及最小示例独立撰写。

主要风险是把潜在 holder 当成已证实泄漏，或将 allowlist 示例误作任意对象安全保证。通过明确可达性、`unverified`、合成数据和合法字段控制约束。缺少真实模型对照时不宣布发现率或效率提升。

回滚以受保护 PR 恢复受影响 Skill/reference/test 和对应版本投影；不重写已发布 tag、资产或历史验证记录。
