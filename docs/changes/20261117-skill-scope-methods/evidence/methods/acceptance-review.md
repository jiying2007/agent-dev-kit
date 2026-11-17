# 方法范围核对（实现者记录）

本记录不是独立 review 或宿主行为认证；最终独立审核由其他 reviewer 执行。针对 7 项修正核对保留的语义与反例：

| 项目 | 方法/源级验收 | 保留的边界 |
|---|---|---|
| perf | ARM PMUv3 的通用 CACHE_MISSES 映射为 L1D_CACHE_REFILL，故不得通称 LLC。入口现在按 CPU/PMU/运行内核映射解释，LLC 结论核专用事件，未知/不支持 unavailable。 | 正确采样、有效负载、等价工作量 A/B、噪声/扰动、无效与无收益仍区分；未测具体 BSP。 |
| artifact | 实际 compiler 将 team-core 导出为 claude-code、opencode；随包参考限定 llm_agent Root helper，普通消费者沿用已核验项目门禁。 | Root 接入仍核适用 helper；缺适用门禁 BLOCKED；无新脚本或安装依赖。 |
| composition | 实际执行发布命令，对照 manifest 的完整 core/optional 路径集合，包含两个嵌套子 Skill。 | 沿用 rg；未改变 canonical matcher、安装器或权限。 |
| growth | frontmatter 和正文均将 trace 候选限定为持久 prompt/Skill/Workflow/AGENTS/记忆晋级；普通建议不需晋级。 | 实际写操作按原任务授权；长期资产仍为候选、审核与验证，不自动保存记忆。 |
| URL | 若 DNS 预检公网、连接前解析变内网，连接只能使用已核地址；重试/fallback 同样受限，重定向重核。 | 原 hostname 的 Host/SNI/证书校验保留；工具不能兑现时沿用无法安全检查即停止。未新增 HTTP 客户端或宣称实网绕过已修。 |
| UBI/UBIFS | 逻辑 layout/hash 相同但 VID/data offset 与目标不符，仍不可交设备；对齐 PEB、min-I/O/subpage、VID/data offset、LEB、volume 对齐/容量。 | 仅相应格式启用；未知留 host；原备份/恢复、operator、readback/boot、单板后扩批边界保留。 |
| human-active | 两人区间 [0,15]、[5,20] 的并集为 20 分钟、合计 30 人分钟；分别记录，不混用不等式或基线口径。 | 单人即并集，无额外多人字段；agent-active 仍为各 Agent 时长之和，不能冒充 wall-clock。 |

## 可追溯来源

- Linux v6.12 ARM PMUv3 映射：https://github.com/torvalds/linux/blob/v6.12/drivers/perf/arm_pmuv3.c#L48 （blob 0afe02f879b45a8600b9cea1bfd88e6a68096a67）；LL cache read miss 在第 72 行单列。
- Linux v6.12 UBI 目标偏移校验：https://github.com/torvalds/linux/blob/v6.12/drivers/mtd/ubi/io.c#L658 （blob a4999bce435f5618986dc9b96f973cf4e64676c0）；data offset 在第 664 行另核。
- OWASP SSRF Prevention：已验证地址须用于连接并保留原 hostname，重试/fallback 同样适用。https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- Python create_connection 对非数字 hostname 再解析的语义：https://docs.python.org/3.12/library/socket.html#socket.create_connection

以上官方资料已在前轮审查实际读取，本轮不把源码反例冒充实网/板端测量。新 tests 中导出与 rg 为真实执行；perf/growth 检查仅为源条款防回归。

## 交付观察

- 新测试注册在既有 tests/test_skill_content.sh，未新增全局测试套件或门禁。
- 基线红：red-tests.txt，4 个 test / 5 个失败子项。
- 语义修正与初次消重后，verified-targeted-tests.txt：43 项通过。
- 最后一次重复自然语言消重后，handoff-targeted-tests.txt：17 项通过；git diff --check 通过。
- 当前 9 个入口/参考文件相对基线净减少 69 B，其中 core entry+refs 净减少 195 B；精确文件摘要见 handoff-file-deltas.json。源字节变化不等于实测 Token 收益。
- profile-ratchets*.json、final-profile-ratchets.json、verified-profile-ratchets.json 是并发编辑期间的原始阶段观察，包含已保留的超限负结果；不作为最终整合资格。最终 8 项由 coordinator 在所有实现冻结后统一核验，原阈值未改。
