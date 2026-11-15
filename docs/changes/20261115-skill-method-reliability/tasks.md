# 任务与验证

当前职责：root 负责合同、整合、证据与受保护交付；deep_task_usability 负责共享状态、发布和 flaky；deep_domain_methods 负责领域方法、Artifact 和接口候选扫描；独立 reviewer 不实现。

| 任务 | Owner | 状态 | Verify |
|---|---|---|---|
| 完整 65 项深审，记录原失败、覆盖与保留理由 | 两位实现分工 / root 汇总 | 已完成：65 唯一项、131 阅读路径 | 两组实际读取清单与 Manifest 56+9 唯一身份逐项对齐，原读取路径与合并基线内容一致 |
| 共享 current-state 字段校验并保留消费者错误码 | deep_task_usability | 已实现；定向 31 项通过 | 同输入调用公开 state-check/resume 的合法上界、越界、重复、严格读取和无执行回归；新增边界测试曾红 7 项 |
| 完整发布历史与 flaky 实际取证示例 | deep_task_usability | 已实现；11 项实际示例回归通过 | 临时 Git 仓首发/正式基线/非发布 tag/错误基线；实际执行最终示例的成功/失败/混合/特殊测试名与合成凭据 |
| CTest 空集、离线抓包及重定位解码修正 | deep_domain_methods | 已实现；领域夹具 43/43（含准备/静态项） | 真实 CTest 的空/禁用/筛空/正常/失败/运行时 skip，真实离线 pcap/坏文件/零匹配，真实 PIE 地址反例与适用边界 |
| Artifact 实现语义与跨文件错误码候选扫描 | deep_domain_methods | 已实现；包含在领域夹具结果 | 隔离 workflow review 的 PASS/拒绝对照与真实多文件扫描；模板字段核对，不冒充完整源码资格认证 |
| 版本候选、全量回归、独立 Spec/Quality 与证据绑定 | root / 独立 reviewer | 11.3.3 已同步；待冻结全量和最终裁决 | strict、既有 8 profile ratchet、完整 tests/run_all.sh、当前源码摘要与独立 finding 收口 |
| 受保护 PR / main CI / promotion / release | root | 待前序完成 | exact HEAD 的必需检查、squash 合并、实际 tag/release/制品状态 |

不得以改变文字数量、扫描命中或模型未执行的 fixture，声称全部 Skills 的模型效果、Token 或时延已提升。

本表是源码冻结前状态；最终全量验证、独立裁决和远端交付随后写入同目录验证/完成回执，不改写此前执行时间。
