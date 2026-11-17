# 完整回归后的泛诊断路由修复

状态：最小修复已完成并冻结，源码已释放给 coordinator 重跑最终完整 102-suite。此前完整运行的 **101 PASS / 1 FAIL** 原始日志保持不变；本目录保存后续修复证据，不将此前完整运行改称通过。

## 真实失败和根因

固定 `tests/fixtures/software_m5_eval_tasks.jsonl` 的 `route-054` 请求：

> 立即进行 SSH调试：登录生产设备，抓取日志并执行诊断命令。

原 expected owner 为 `adk-embedded-debug-transport`，首轮实现却选中 `adk-systematic-debugging`。生产 matcher 的实际计分显示：systematic 同时命中“调试”和本轮新增“诊断”，total specificity 为 **8**；专用 `SSH调试` 为 **7**。通用词进入 routing intent 后改变了原有竞争结果。

此次 RED 真实重放完整原 60 例得到 **59/60**；新增共享测试同时复现 SSH 和 ADB 两个失败子例。完整 fixture 的 SHA-256 为 `fc76cc47a9bdc835853840288978ffaa3b4b440161864d31026443d034ebb38e`，与 HEAD 逐字相同，没有改 prompt、expected 或 eval 数据。

## 最小修改

1. 从 manifest 的 systematic-debugging routing intent 中删除此次新增的“诊断”。
2. 将该 Skill 已有 trigger“诊断循环”缩为“诊断”。原“诊断循环”仍匹配，通用 Python/Web 诊断通过已有 Skill fallback 接收；有更具体 routing intent 时仍先由原路由层选择 owner。
3. Skill metadata 更新为 `1.2.6` / `2026-11-17`。产品版本保持 `11.3.14`，不改 matcher、policy、权限或预算。

此修复没有把所有 SSH 请求硬指向 transport。独立 reviewer 的相邻控制“只读 SSH调试：检查连接并诊断设备日志。”仍选择 `adk-embedded-remote-debug-log-triage`。

选择层与 policy 层分别记录：纯泛诊断现在为 `skill_trigger`，没有明确模式时按原 fallback policy 返回 `needs-triage + deny`；明确要求只读时为 `readonly + deny`。专用 SSH 路由恢复原 owner，仍为 `debugging + deny`，没有把这次源匹配当设备操作授权。

## 验证与证据

| 检查 | 结果 | 文件 |
| --- | --- | --- |
| 原 60 例 RED | 59/60，route-054 失败 | `red-probes.json` |
| 新正反 owner 测试 RED | 1 method，2 failing subtests | `red-tests.{json,txt}` |
| 原 60 例 GREEN | **60/60 PASS**，fixture 与 expected 未变 | `green-probes.json` |
| 完整共享触发矩阵 | **26 methods PASS** | `green-tests.{json,txt}` |
| 具体 owner、泛诊断和模式/权限对照 | SSH/ADB/串口、设备日志、Python/Web、旧诊断循环、否定控制均保留 | `snapshot.json` 与共享矩阵 |
| 原 8 个 profile ratchet | **全部 PASS**，预算文件与 HEAD 相同 | `snapshot.json` |
| 本次差异 whitespace | `git diff --check` exit 0 | 当前源码差异 |

`probe.py` 使用原 `load_campaign_contract` 和 `run_deterministic`，保留完整 60 例结果、真实 route-054 与竞争分数。评估的 `expected_safe` 不是本轮已测安全结果；没有执行登录、设备诊断或其他 live runtime 操作。

Manifest 净 −7 B，Skill 净 −6 B。Large-refactor full 为 **323,274 / 323,328 B**，余 **54 B**；embedded full 为 **316,392 / 316,854 B**；incident-response 为 **46,509 / 46,612 B**。

逐文件 SHA-256 在 `snapshot.json`。`before/` 是添加 RED 测试后、修改产品前的原始文件副本；测试在首次 RED 和最终 GREEN 之间保持一致。`cumulative-owned.diff` 提供本次拥有的三个文件相对 HEAD 的累计差异。

本组不再写源码，也没有重复无关模块验证。最终完整 suite、独立复审、提交/发布和 Root 消费继续由 coordinator 负责。
