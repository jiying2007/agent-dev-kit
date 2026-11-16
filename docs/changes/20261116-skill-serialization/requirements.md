# 目标与验收

在已完成全体 65 Skills 审查的 v11.3.10 上，补齐第三方资产安全审查中的隐式序列化路径。此变更来自本轮外部原始 Skill 对照与标准库反例；不以全覆盖为由重复修改已满足要求的 Skill。

## 目标

- R1：已有 `adk-security-supply-chain` 在适用的源码审查中识别 credential holder、生成的 serializer 与日志/追踪/响应等 sink，并检查当前 diff 之外的另一端。
- R2：明确 `repr=False` 仅影响 repr，不能证明 `asdict` 或其他序列化输出安全；嵌套对象也需要按实际输出路径检查。
- R3：只在所审资产涉及相应类型或整对象输出时加载细节。保留 source-only/adoption/runtime 三种范围，不引入新 Skill、路由、扫描器、运行依赖或统一追加门禁。
- R4：演示与验证只使用合成 sentinel；在受控输出中确认敏感值被排除，同时保留必要的非敏感字段。报告只写路径、符号和结论，不回显凭证值。
- R5：未证明 serializer 到 sink 可达时报告 `unverified`；没有字段名称命中不构成无泄漏证明，不自动执行不可信候选代码。

## 验收

1. 从最终发布 reference 提取的可执行示例实际区分 repr、asdict/嵌套输出与显式 allowlist，并验证合法字段保留。
2. Skill 主入口提供有条件的 reference 导航；导出后 reference 与正文仍可用，原 line/profile 字节阈值不变。
3. 现有完整回归通过；独立只读 Spec/Quality review 无未关闭 blocker/major；真实失败及修复分别保留。
4. 受保护 PR、精确主线 CI、不可变发布和消费端 source-only 接入全部取得各自回执；源码检查不冒充模型 A/B、Token 降幅或运行态认证。

## 非目标

不导入外部 Skill 的完整正文或脚本；不自动安装、执行第三方包；不扩大供应链 Skill 到全部产品安全任务；不新增模型调用、付费评测、定时巡检或设备操作。
