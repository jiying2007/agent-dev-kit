# T3b 实现交付

状态：本组实现及定向自测完成，文件已释放给 coordinator。基线 `78c3be7f6f9b5ee2e557de54156532fb3169198d`，分支 `feat/skill-usability-20261117`。本组没有提交、push、调用 live runtime 或操作设备。这里是实现者自测记录，不能代替最终独立 Spec/Quality 审查。

## 审查与授权边界

`report.md` 已冻结 25/25 workflow Skill 覆盖：完整读取 25 份 SKILL.md 和 35 份支持文档，区分实际失败、静态矛盾和观察。四项实际缺陷 W01–W04 被主合同采用为 U03/U04/U01/U02。本组明确排除了 human approval 假阳性：规则晋升的人类批准与明确委派的最终 Spec/Quality 审查不是同一动作。ADR 动作/话题冲突及 cross-team 的 intentional explicit-only 保留为观察，没有扩展本次实现。

收到 coordinator 的 T3b 任务后，本组明确由 reviewer 切换为 implementer。本次只写分配的 routing、validator、4 个 Skill 和 task reference、共享触发测试与两个现有测试入口。A 的 BSP/RTOS/DMA 源文案和 C 的导出/归档/信封文案由各自作者维护。

## 实现结果

| 合同 | 最小修改 | 正反验收 |
| --- | --- | --- |
| U01 | 将“代码评审”从 commit gate 触发移交 review-loop，并在既有 review routing intent 接收该同义词。 | 普通代码评审、局部意见核验和原独立代码审查进入 review-loop；commit message 与提交前检查仍由 commit gate 接收；否定 review 不被重新选入；mutation permission 保持 deny。 |
| U02 | generic 诊断进入既有 systematic-debugging intent；现场 readiness 使用已有 implicit_context 和具体现场/OTA 动作，移除与设备状态机教学重合的触发。 | Python/Web 诊断、数据库回滚、纯状态机和引用中的 OTA 不选现场 Skill；量产产测、现场诊断、OTA 回滚及既有生产现场 fixture 保留；显式只读不升级权限。 |
| U03 | canonical v2 保持原 19 字段。随包 reference 提供完整可解析 JSON、类型和四类 work item 的权限/exit gate 表；主文压缩重复清单并指向 reference。 | Claude Code 与 OpenCode 实际 compiler 输出各自解析随包样例，再由原生产 validator 接受；scope_read/scope_write/global_constraints/interfaces 保存在 constraints 字符串条目；外层 owner/DAG/ready/worker/report 不混入 v2；五个错误顶层字段与 owner 均拒绝。 |
| U04 | kind/retention 在 hash membership 前判定字符串；prototype artifact 跨字段检查仅在有效 string array 上迭代；相邻 prototype validator 同样拒绝非字符串 retention/expiry，不再把整数 expiry 强转为字符串。 | research 和 prototype 的 artifacts/kind/retention 错误 JSON 类型返回非空 errors tuple；有效四类 work item 仍通过；错误权限/exit gate、缺 prototype evidence、过期记录及不安全 orphan 均拒绝。 |

没有修改 matcher 核心、canonical required fields、schema 枚举或权限合同。没有靠增加 top-level 字段兼容原错误示例。机器包不可验证时必须标记未验证，信封本身不能成为授权来源。

共享触发矩阵还纳入 A 的限定案例：真实 BSP 梳理、原 SoC board 迁移分析、BSP 移植/实现驱动邻居、RTOS 领域与明确无 RTOS、两个 DMA/CPU-budget 正例和纯轮询排除。保留既有 fallback，不增加重复 BSP routing intent。

## 现有测试入口

- `tests/test_intent_boundary_governance.sh` 注册 `test_task_package_delivery.py`，由已有 intent boundary owner 同时检查真实导出样例和类型拒绝。
- `tests/test_skill_content.sh` 注册 C 的 `tests.test_skill_consumer_usability`，沿用已有 content owner；不新增顶层 gate，不重复注册。
- 共享 `tests/test_skill_trigger_matrix.py` 加入本组及 A 的正反矩阵。

## 验证与原始输出

| 阶段 | 结果 | 原始记录 |
| --- | --- | --- |
| 冻结源码既有定向测试 | 53 methods PASS | `existing-tests.{json,txt}` |
| 新验收首次 RED | 7 methods；19 failing subtests、14 errors | `implementation-red.{json,txt}` |
| 首轮 GREEN 尝试 | 47 methods；1 failing subtest | `implementation-green-attempt-1.{json,txt}` |
| 修正后定向组合 | 47 methods PASS | `implementation-green.{json,txt}` |
| 现有 content gate（含 A/C） | 211 methods PASS，exit 0 | `skill-content-gate.{json,txt}` |
| 现有 intent boundary gate | 原 5 + 新 4 methods PASS；原脚本断言和官方文档治理检查通过，exit 0 | `intent-boundary-gate.{json,txt}` |
| 完整既有触发矩阵 | 24 methods PASS，exit 0 | `trigger-matrix.{json,txt}` |
| 定向 Ruff | PASS，exit 0 | `t3b-ruff.{json,txt}` |
| 本组 tracked diff whitespace | `git diff --check` exit 0 | 本组最终差异 `t3b.diff` |

首次 GREEN 的唯一失败是“不涉及量产或 OTA”的并列否定被宽泛 OTA 上下文重新接收。修复改用具体 OTA 升级/回滚/验收上下文，既保留该负例，也验证“不涉及量产，只读评估 OTA 回滚”正例；没有改核心否定 grammar 或添加语言黑名单。

默认 Python 的 `-m ruff` 曾返回 `No module named ruff`；保留在 `t3b-ruff-unavailable.{json,txt}`。随后使用已有 `verification-tools/adk-quality-venv/bin/ruff` 成功，没有安装依赖或将环境失败当产品失败。

`verify_implementation.py` 可重放四个现有门禁/检查并保存原始输出；命令、cwd、退出码和时间在各 JSON 中。可按 gate 名称只重跑需要的一项。源码审查 `reproduce.py` 绑定冻结基线并拒绝 dirty source，避免用新实现覆盖原始审查结果。

## 字节与交接

`t3b-source-delta.json` 固定本组 11 个文件的逐文件 SHA-256、基线/当前字节与差异，`t3b.diff` 包含 tracked 修改及新测试文件。此次 Skill/reference 源资产净 **+140 B**：task 主文 −782、task reference +750、production +172、review +19、commit −19。数字为源字节，不能推断 Token、调用次数或实际效率。

Manifest 的 routing 写入已经停止；coordinator 可继续版本包装。本组不再写入其余已交付文件。所有 8 个原 profile ratchet 未被本组修改；最终合并后的 profile 测量、完整 regression、精确源码独立终审、组件发布及 Root 消费由 coordinator 负责。上表是执行时的组合工作区快照；C 在其 reference 的后续等价压缩须纳入最终冻结验证。

本轮证据覆盖源码 matcher、真实 compiler 目录和生产 validator；没有原生模型运行、live dispatch、板测、刷写或设备资格证据，也没有把这些能力宣布为通过。
