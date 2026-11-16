# 负结果与排除路径

- knowledge/L2-domain/lessons.md 在当前 ADK 不存在。Knowledge Provider 和 Execution Policy 未提供可用外部入口；不虚构历史教训，沿用已授权的 source-only 工作范围。
- 创建独立工作树首次因原 ADK checkout 尚未取得合并提交 fad9d4d1 返回 exit 128（invalid reference）；fetch origin main 后重试成功，未修改原工作树或降低源码身份要求。
- 父线程读取了猜测的 fault-recovery-details.md 路径，实际不存在；已以真实 SKILL.md 核验该 Skill 无该 reference，不将审计命令错误记为资产缺失。
- 六个嵌入式实现 Skill 当前方法及八项定向检查无新反例，保持 KEEP。诊断 harness invocation 观察未找到真实解析 consumer，继续 OBSERVE。
- 原 IMAP 本地探针还含完整地址对照，本变更只采用精确时间分支。±02:00 夹具中的候选扩展只对其固定输入成立，不提升为通用前后一天算法。
- 原 fault probe 的配置未命中、错误清理均为有意构造的控制；原 IMAP 缺失时间返回也是故意的无效/不完整协议夹具。不将它们称为 ADK 现有代码漏洞或真实服务器故障。
- 准备工具时有三次 exit 2：读取旧 scratch 目录下不存在的 build_tree_packet.py、猜测 Root 的 promote-agent-dev-kit.sh、以及在实施目录尚未创建时列举文件。已分别用 rg 定位当前 scratch 的真实 helper、Root 的 scripts/promote-adk.sh，并等待实施者交接；这些是路径/时序错误，不是产品资产缺失。
