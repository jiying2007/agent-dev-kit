# ADK 8.2.0 源码候选独立 Spec / Quality 与 Harness 七维审查

- 审查时间：2026-11-03T02:34:50Z。
- 真实 reviewer identity：`ai/root/review_goal`，当前 Codex 独立子代理执行上下文 `/root/review_goal`；kind=ai，independence=independent。本代理未实现或修复待审代码，未编辑仓库，仅按主代理明确委派进行只读审查并生成本报告。不是人类审批或另一位仓库 owner。
- 委派边界：实际读取 `.adk/review-policy.json` 与 `.adk/review-authorization.md`。owner-delegated-ai 允许 source-change 和 harness-source 审查；本轮用户又明确要求“检查，没问题就提交、推送合并、应用”。本报告不代替 protected CI、签名、制品身份、正式导入、source-to-live 回执、设备或产品资格。
- Review Target：working-tree / whole-diff。HEAD=`e94e15a462b394a6ba5b4c4c8c1fc6a7a5a7088b`，候选版本8.2.0。
- 当前28个变更文件按排序后的 `path UTF-8 + NUL + SHA256(file bytes)` 串联取SHA256：`afbf2919f4de5576e1a487efe251beedd329774e364f8c50682c82a14d585cdb`。包含未跟踪文件；不是只审已跟踪diff。
- latest_worktree_reviewed=true；本报告之后的源码变更需要重新核对快照。审计记录或Harness metadata装订不能替代源码审查。

## 实际审查方法与复用边界

本代理逐项审查本次 Goal authoring / 当前状态完整增量，包括typed core、CLI路由、Skill正文与示例、manifest注册、profile增长、内容/关系契约、测试注册与反例、需求/设计/任务/验证文档。首轮发现三项major并要求修复，第二轮已独立确认修复。本次补充检查新增stage_order=15、8.2.0所有版本投影、CHANGELOG和任务说明，未扩大Goal预算或执行权限。

对Harness，重新读取完整七维 evaluator `readiness.py`、合同 `manifests/harness_readiness_contracts.json`、review policy与authorization、`review_evidence.py`主要身份/范围/来源校验控制流、`readiness_evidence.py`读取/合同边界，以及根AGENTS和rollback实现。旧8.1.5独立报告与来源列表只作为明确归属的历史语义审查输入：其63个绑定source当前55个逐字节相同，8个变化均为本次已读版本/manifest/CHANGELOG投影。三个validator依赖指纹逐项确认不变。本次不是对整个仓库所有实现重新从零审计，也没有把旧CI结论更新日期冒充新执行。

## 源码问题闭环

1. M1 major / fixed：选中open交付项曾可绕过未关闭依赖。当前批次检查对所有选中open/ready项约束依赖closed，新增确定性反例覆盖。
2. M2 major / fixed：新入口曾绕过严格JSON，深嵌套抛未捕获RecursionError，特殊文件可阻塞，且哈希二次无界读取。当前复用strict_json有界普通文件读取与严格解析、拒绝链接路径，并直接哈希同一次原始raw；深度、NaN、溢出、非法Unicode、FIFO/目录/链接和无二次读取已有反例。
3. M3 major / fixed：标准state-check接受的work_in_progress曾被plan-check/resume拒绝。两个入口现复用valid_work_in_progress，正负值一致验证。
4. 分类键冲突由主代理机械验证发现后最小修为stage_order=15；本代理复核当前manifest排序键与相关注册，没有新增冲突语义。

当前 blocker=0、major=0、minor=0。本补充轮新增finding class=0，reopened=0；Contract Change Decision=none。Spec PASS / Quality PASS，范围仅为本次源码及七维repository-source语义。

## Harness七维度独立判断

| Dimension | Spec | Quality与证据边界 |
|---|---|---|
| context_legibility | PASS。根AGENTS和README入口仍精简，Goal技能正文清晰区分合同生成与实际执行，8.2.0声明准确。 | PASS。唯一原目标/当前状态、按需历史和真实CLI入口保留；当前raw evaluator pass，无blocker。 |
| spec_and_execution_contract | PASS。两组本次requirements/design/tasks、父验收映射、有限batch、验证/停止/重规划字段可对应实现；版本投影统一8.2.0。 | PASS。依赖绕过负例已修复，合同lint只声称结构检查，不声称原验收语义已完成、实际证据已验证或预算已设置；raw pass。 |
| tool_and_permission_boundary | PASS in source scope。新CLI只读，不执行合同中的verify命令、不调用宿主Goal、不写设备或扩张权限；policy/authorization与validator未弱化。 | PASS in source scope。严格JSON、普通文件有界读取、链接拒绝、同次字节哈希有实际负例；当前repository raw tool evaluator为not-applicable，不是实际MCP运行权限或安全认证。父路径链接检查仍是preflight，并不声称对恶意并发rename具有原子性。 |
| state_and_knowledge_continuity | PASS。保留原Goal身份、累计和验收分母；唯一current-state恢复与可选work_in_progress兼容，不加载历史正文。 | PASS。共享WIP验证避免入口分叉；completion_allowed/evidence_contents_verified保持false，state与batch状态不能冒充宿主完成；raw pass。 |
| verification_review_and_eval | PASS。新测试加入既有test_execution_policy.sh；真实外cwd CLI、正负合同、严格输入边界与独审发现均有回归。 | PASS as source。本代理当前重新执行44个goal/state/strict测试全部通过，diff-check通过。raw pass；正式当前Harness gate仍needs-review（7项invalid_delegated_review），不是green CI。新记录装订后需另验证record与exact-HEAD完整CI。 |
| recovery_and_rollback | PASS。新合同只读且预算提案未应用，失败可诊断；变更设计有精确撤回范围，现有backup-rollback入口未改变。 | PASS。保留原历史、原Goal累计及用户dirty，不盲重试外部阻塞；当前raw pass。实际runtime回滚和发布回滚尚不能由源码报告证明。 |
| freshness_and_entropy_control | PASS。ownership、格式/catalog/freshness机械入口保留；新增Skill按manifest路由、当期有限批次和延迟reference组织。 | PASS as source。source-growth ratchet只按新增资产精确增量，既有内容增长限制仍生效；当前raw pass且无scan blocker。不声称本轮更新全部外部引用新鲜度或已测得token收益。 |

## 当前实际执行证据与负结果

- 2026-11-03T02:34:50Z附近，本代理再次执行test_goal_authoring、test_planning_state、test_strict_json：44 tests PASS。
- `git diff --check` PASS。
- 当前七个raw evaluator：context/spec/state/verification/recovery/freshness均pass，tool not-applicable；raw blockers共0。
- 当前真实 `run_harness_readiness(..., mode="gate")`：overall needs-review，七维均因旧来源review产生invalid_delegated_review。本报告不将此负结果改称通过；后续新record/metadata必须按当前字节装订并实际验证。
- 旧8.1.5 record的63个sources中55个哈希不变，8个已读变化为.version-lock、CHANGELOG.md、CONTEXT.md、README.md、manifest.json、manifests/software_m5_eval_contract.json、pyproject.toml、src/agent_dev_kit/__init__.py；review_evidence.py、strict_json.py、readiness_evidence.py指纹全部仍与旧record相同。
- record引用总预算64保持不变；当前44 raw scan refs与全部28 dirty的并集为71，后续装订应选择必要source及保留完整增量审计指针，不放宽validator限制。

**最终独立源码裁决：Spec PASS，Quality PASS。** 这是AI独立源码与Harness七维语义结论，不是人类APPROVE、当前CI成功、可绕过分支保护、不可变release已签名、Codex运行态已应用、业务Goal已恢复、token收益或设备/产品放行。
