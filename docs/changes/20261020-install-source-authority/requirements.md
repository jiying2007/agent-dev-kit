# 安装升级与历史恢复的来源权威

## 目标

修复候选 manifest 被误用于验证旧版 receipt 的升级阻断、release rehearsal 缺少 rollback manifest，以及 target 文档到期后阻断完整历史恢复的问题。公开说明与原生 Python 3.8+ 支持合同保持一致。

## 验收

- AC1：不同版本 A → B → A 通过真实 plan/apply/rollback，逐文件字节、权限模式和原 receipt 字节恢复；首次安装及同版本重装保持有效。
- AC2：旧 receipt、旧备份与候选资产分别由显式选择的精确源码验证。缺失或错误旧来源、篡改/遗漏 receipt 库存、重算 digest 后的备份篡改、mode 漂移、路径替换均在任何目标文件变更前拒绝。
- AC3：回滚和升级对旧库存的重现不因 target 元数据自然到期而失败；新 plan、apply、export、target check 仍执行当前 freshness。receipt 时间字段不能作为可信历史时间证明。
- AC4：`release rehearse` 通过真实不同版本 artifact 的正向安装、升级、回滚路径，报告仅在文件字节、mode 和 receipt 完整恢复后通过。
- AC5：Python 3.8+、按解释器固定的依赖、严格启动门槛在 README、usage、commands 一致。所有 Python 代码保留原生 3.8 兼容。

## 范围

保留 plan v2、receipt v3、当前收据权限、路径约束、原子替换和失败补偿；不自动发现或下载旧源码，不从可编辑 plan/receipt 读取源码路径，不新增 runtime/native/Owner/签名资格，不改变受管资产删除策略。版本与远端提交、CI、合并由主任务统一处理。
