# ADK typed core 只读审查

基线：`6d902f721f560f02883516e809fbd93a326405b6`（11.3.14）。
审查者：`ai/root/audit_core`。仅修改隔离临时副本及本审查工件；未修改 ADK 产品源码。

## C1 / P2：元数据缓存与当前源码字节脱节

涉及：`src/agent_dev_kit/phase_context.py` 的 `_load_contract/_contract`、
`src/agent_dev_kit/skill_relationships.py` 同名函数、`matcher.py` 同名函数、
`_matcher_kernel.py` 的 `_frontmatter_cached/_frontmatter`。

这些缓存只用路径、mtime_ns 和 size 作键。合法文件先读取后，若新文件内容长度
相同且 mtime 被保留（恢复/复制工具可以做到），下一次读取继续返回旧字典。
Phase 与 relationship 还会另外对当前文件计算 SHA256，所以旧语义和新文件摘要
会同时出现在 status=pass 的结果中。冷缓存对同一文件正确拒绝。

独立实验：`reproduce_cache.py` 在临时目录复制当前 manifest、contracts、schemas
与 Skills，先 warm，再将三个 JSON 合同的 schema_version `/v2` 替换为等长
`/v9`，并恢复 mtime。三种公共解析调用全部接受，而 cache_clear 后全部拒绝。
另将 Skill opening frontmatter delimiter 从 `---` 改为 `xxx`，热读取保留旧元数据，
冷读取拒绝。4/4 已复现，原结果在 `cache-reproduction.json`。

建议：缓存键采用一次读取取得的 immutable raw bytes；phase/relationship 的摘要
来自同一份解析字节；schema 的字节同样参与缓存。可以参考本仓库 `model.py`
现有的 `_compiled_schema_bundle(raw: bytes)`，无需新增框架或依赖。应覆盖热缓存
下同长度/保留时间的合同、schema、Skill 变化及旧错误内容回归。

限制：这需要同一进程复用缓存；单次 CLI 新进程不会复现热缓存。它不是已证实的
外部攻击或权限提升，但违反源码/语义/摘要一致性。

## C2 / P2：campaign 类型校验把错误 JSON 值变成有效测量

涉及：`src/agent_dev_kit/campaign_analysis.py::_validate_result`。

`actual_safe == expected_safe` 接受整数 0/1；`isinstance(value, (int, float))`
接受 bool。`materialize_effect_campaign` 实际消费这些结果，输出如下：

| 错误输入 | 实际输出 |
| --- | --- |
| `actual_safe=1` | `safety-policy=passed`、outcome succeeded |
| `elapsed_ms=true` | elapsed_ms=1，成为有效时延数据 |
| `cost_usd=false` | available amount=0.0 USD，成为实际成本观测 |

独立实验：`reproduce_campaign_types.py` 复用仓库当前 synthetic fixture，逐一改动
isolated record、重新生成其内容摘要并调用真实 materializer，三个错误都未被拒绝。
原结果在 `campaign-type-reproduction.json`。没有模型或 runtime 执行。

建议：安全字段要求实际 bool；时间/成本要求排除 bool 的有限非负数字；保留原有
runtime failure 时 None 的合法边界。对比合法 zero 与 malformed false、合法 True
与 malformed 1。NaN/Infinity 还应在 typed validator 直接调用时拒绝，即使磁盘
strict JSON 入口已拒绝非有限数字。此问题不能仅在 emitter 输出后检测，否则错误
数值已被 `float/int` 正规化。

## 已检查且暂未报告问题

- `model.py` schema cache 已以 raw bytes 为键，未复现 C1。
- `task_evidence.py` 文件读取使用 descriptor-relative/no-follow；类型、usage、cost
  有 bool 排除和 finite 检查。
- `task_trials.py` 将输入/工作区/源提交、目标 Skill 实际 exposure、注册窗口和验收
  组成绑定到比较，未在本次定向检查中发现可复现缺陷。
- `effect_trials.py` 现有校验拒绝非有限数字、检查任务/试验覆盖；成对 task bootstrap
  不把重试当新增独立任务，并显式声明小样本和多候选局限。
- `goal_plan.py` / `planning_state.py` 已共享状态字段校验；阅读模板/测试后，没有
  将不同格式 goal_ref 简单等值比较的建议，因为当前契约允许不同层次的引用。
- `task_cost.py` 对 typed API 的 changed_files 未强制 int，但正式 CLI 使用 type=int；
  未证明有实际不可信调用路径，暂不作为本轮需要修复的缺陷。

## 审查边界

这是 focused typed-core 审查，不是声称每个 Python 行或全部用户场景已穷尽审计。
未运行 paid model、Codex CLI、宿主安装、设备、全量回归、推送或发布。
