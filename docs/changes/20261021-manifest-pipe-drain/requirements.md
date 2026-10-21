# Manifest 流式存在性检查修复

## 冻结目标与边界

修复 Manifest 查询接入提前退出匹配器时，将存在的名称误判为不存在的缺陷。保持公共 shell helper 返回值、精确匹配和静默 stdout；真正的上游读取或解析失败仍必须使检查失败。

本轮只涉及共享 Manifest shell consumer、goal/capability consumer、external handoff guard consumer 与对应确定性回归，组件补丁版本前移至 8.0.37。Root 文件式 grep、Python 错误策略、运行时与资格门槛不属于修复范围。合成查询 fixture 不是 Native、现场或模型效果证据。

## 风险与验收

- 最早一项命中后仍完整读取超过管道容量的尾部，不产生 EPIPE 或错误的 unknown 引用。
- 五个公开存在性 helper、goal/capability 与 handoff guard 检查的大清单成功路径可重复通过；缺失名称/guard、损坏 JSON、匹配后上游非零退出仍失败。
- 测试覆盖固定字符串、整行和以连字符开头的名称，stdout 仍为空。
- 真实旧实现复现与新实现结果分别保留，不把本轮诊断追认为 2026-10-20 历史异常的精确根因。
- 共享逻辑执行完整 ADK 回归、独立 Spec/Quality 审核及受保护主线 CI；正式组件 release 验证后再由 Root 固定精确身份。

## 产物

源码补丁、确定性测试、设计与验证/负例报告、独立审核记录、受保护 PR 与不可变组件发布。没有真实运行证据的资格项继续保持未通过。
