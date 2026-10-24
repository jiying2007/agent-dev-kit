# 发布 bundle 完整性

## 目标与边界

修复 2026-10-24 全面审查 F1：canonical release validator 与发布前断言必须拒绝缺失或被修改的预编译 bundle。冻结基线为 `415590db44e88979185efb850e2339a3f95411ef`。用户已授权按建议全部优化落地，含既有受保护提交、审核和发布流程。

保留现有 release manifest、三资产、签名和 immutable release 权威，不新增发布框架，不把当前正式产物认定为损坏。风险层级 E3；实际运行与产品资格不由本变更授予。

## 验收

- 干净真实构建通过；篡改 Skill、删除全部 bundles、缺少 target、增加/删除文件、模式漂移均失败关闭。
- 修改或重算待验包自有 manifest 不能替代受验证 source 身份。
- 有界归档、路径、重复、链接和 source 校验既有行为继续成立。
- 完整回归、独立只读 Spec/Quality 审核与精确提交 CI 通过后才发布。
