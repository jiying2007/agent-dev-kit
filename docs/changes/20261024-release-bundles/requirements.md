# 发布 bundle 完整性

## 目标与边界

修复 2026-10-24 全面审查 F1：canonical release validator 与发布前断言必须拒绝缺失或被修改的预编译 bundle。冻结基线为 `415590db44e88979185efb850e2339a3f95411ef`。用户已授权按建议全部优化落地，含既有受保护提交、审核和发布流程。

保留现有 release manifest、三资产、签名和 immutable release 权威，不新增发布框架，不把当前正式产物认定为损坏。风险层级 E3；实际运行与产品资格不由本变更授予。

## 验收

- 干净真实构建通过；篡改 Skill、删除全部 bundles、缺少 target、增加/删除文件、模式漂移均失败关闭。
- 修改或重算待验包自有 manifest 不能替代受验证 source 身份。
- 有界归档、路径、重复、链接和 source 校验既有行为继续成立。
- 所有归档 source 中实际可达的 JSON Schema 均须在引用解析前通过同一离线检查，包括 Native receipt schema；不能由包内 schema 触发网络请求。
- support root 必须在 exists、遍历和读取之前通过独立的资产目录边界检查；归档可改写的 schema 不能充当文件系统访问授权。
- 归档内 Native registry 不能授权宿主程序执行。公开 release validator 必须在调用 managed Native verifier 前拒绝 runtime conformance；不提供跳过信任校验或允许归档执行的公共开关。
- 正常本地 target admission、安装恢复等已授权 managed Native 路径保持原语义。当前正式静态 target 包及 v8.0.39 整包继续通过；没有独立可信 Native 执行授权的 runtime 归档明确失败，不能降为 static 或宣称 Native 通过。
- 完整回归、独立只读 Spec/Quality 审核与精确提交 CI 通过后才发布。
