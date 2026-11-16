# 独立设计核验

Reviewer：embedded_methods（AI，只读独立角色）；基线 fad9d4d170a97c5dbb2c5261432fa2120bfcc3c9。

结论：可进入 Build，无设计级阻断。这是设计核验，不代替冻结源码的最终 Spec/Quality 审查。

已读取四份 change 合同、两个原 Skill、两组探针源码与结果；fault probe 原文 hash 与既有 receipt 一致。未修改实现、未重跑原探针或全量测试。

- 验收与证据相称：两个候选均为方法增强，不把受控模拟程序的问题归为 ADK 运行态漏洞。
- 范围及预算：故障注入基线 3559 bytes，不增字节、不挪减其他 Skill、不提高 Profile 限额；IMAP 仅增强精确时间分支，保留普通日级、只读、UID、预算与 partial；完整地址匹配不纳入。
- 回归须隔离时间条件。原 IMAP 探针的精确结果同时包含地址筛选，不能直接充当仅时间增强的期望。
- 原 IMAP 探针未执行非法时间和预算耗尽；新回归须实际触发这些分支并保留成功与未判定项。普通日级控制实际走日级路径。
- 故障命中证据不可用时保持未知，不用非零返回或健康 follow-up 推定命中，不填零检测/恢复时延。

测试边界：host C 和本地 imaplib 协议夹具不证明设备/HIL、真实邮箱服务器一致性、SLA 或成本收益。最终审查仍需读取冻结后实际实现、控制、旧合同保留、聚合、导出及预算证据。

读取纠正：审查最初尝试了不存在的 optional-skills/adk-email-imap-fetch/SKILL.md，随后按真实 optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md 完整读取；未将路径误猜记录为资产缺失。
