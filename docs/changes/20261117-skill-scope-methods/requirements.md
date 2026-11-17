# Skill 适用范围与方法精度

## 目标与来源

用户于 2026-11-17 明确要求“按建议全面优化落地”。承接对 ADK 11.3.12 / 0973b9dce75e7bde289a9915fc58dfd53cb79b0d 的 65 项审查，落实 5 个明确问题与 3 个条件性说明。既有提交、推送、合并及自动独立审核授权继续适用。

## 验收

1. 通用非嵌入式单测不隐式进入 MCU/RTOS Skill；MCU、嵌入式 Python host 与 Rust 合法测试保留。显式选择不提升权限，原 Fit Gate 继续适用。
2. perf 通用 cache-misses 不再被通用标成 LLC miss；LLC 结论绑定目标 PMU/内核事件映射。
3. artifact-gating 的 Root 专属 helper 仅对真实 Root 接入适用，独立 team-core 导出消费者使用其已核验项目门禁。
4. 组合扫描命令完整覆盖 65 个入口，包括 9 个 optional 中的两个嵌套子项。
5. growth frontmatter 与正文一致：长期规则晋级才进入 trace-feedback-eval-handoff；普通已授权工程改进不额外晋级。
6. URL 方法要求实际连接、重试、fallback/重定向使用已核地址并保持原 hostname 的 Host/SNI/证书验证；依托现有工具，不新增客户端。
7. UBI/UBIFS 迁移按适用性核目标与镜像几何参数，保留现有 operator 边界。
8. 多人试点区分经过/并集时间与合计人时，单人场景保持简洁。
9. 原 8 个 Profile byte ratchets 保持不变并通过；旧成功/拒绝路径保留。
10. 完成必要回归、独立 Spec/Quality 审核、不可变发布与 Root source-only 接入；不继承 runtime/product 资格。

## 非目标与证据边界

不增加 Skill、Agent、平行路由、客户端、巡检或预算硬限制；不扩大授权。Goal/loop/context 的既有协议继续使用，确定性检查和局部 forward observation 不冒充原生宿主认证、配对模型 A/B 或 Token 收益。禁止新增外部付费模型、Codex CLI/Cloud/Work 开发任务。实际模型 usage、设备、真实网络客户端及现场证据不足继续 not-measured。
