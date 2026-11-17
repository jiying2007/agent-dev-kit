# 阶段性独立审查（未冻结，非 canonical 通过记录）

- 审查者：`independent-reviewer-routing-context-20261117`；仅审查与临时证据写入，没有修改产品代码。
- 基线：`6d902f721f560f02883516e809fbd93a326405b6`。
- 已读：根 `AGENTS.md`、`docs/agent-operating-rules.md`、`.adk/review-policy.json`、`.adk/review-authorization.md`、delegated-review runbook，以及本轮 requirements/design/tasks。
- 已审核心 diff：phase_context、skill_relationships、matcher 的 contract loader；_matcher_kernel 的 frontmatter loader；campaign_analysis；对应三个测试文件。
- 状态：routing 工作尚未冻结，本文件不对整个变更作 Spec/Quality 最终裁决。

## 发现 IR-1：有限输入聚合仍产生无穷耗时（major / open）

`campaign_analysis._validate_result` 对每次 `elapsed_ms` 调用 `math.isfinite`，却直接对所有浮点耗时求和返回结果。
两次 `1e308` 都是合法 JSON 的有限正数，均通过逐项检查，但返回 `elapsed_ms=inf`、`latency_complete=True`、`passed=True`。
这违反本轮验收 7 的“耗时只接受有限合法数值；坏输入不得成为真实耗时观测”。

同一路径对 `elapsed_ms=10**400` 直接调用 `math.isfinite(int)` 时抛出 `OverflowError`，未按既有消费者期待转换为 `ManifestError`。
`check_campaign` 仅捕获 `ManifestError`；materializer 随后对总耗时 `round/int`，也不能处理无穷值。

独立、无模型原始复现：`probe_campaign_numbers.py` 和 `campaign-number-probes.json`。普通有限数字通过；bool、NaN、单次 infinity 均正确拒绝；超大整数异常类型及聚合溢出分别如上。
建议修复：在既有准入点明确处理数值转换的 overflow，并对求和后的耗时验证有限性；以两类输入加回归，不改变有效运行错误/缺失成本的语义。

## 缓存源码阶段结论

四个缓存维持原有容量（8/8/8/512），键改为实际读取的 bytes；phase/relationship 的 schema bytes 同时参与缓存键。
这消除了按 path/mtime/size 复用旧内容的明显原因；两个 contract 摘要直接对送入解析函数的同一 `raw` 计算。
错误路径对读取、Unicode 和 JSON 错误做了明确转换，frontmatter 的错误仍补入实际路径。
检索调用点未发现需要迁移的外部公共调用；旧的私有 `_load_contract` 测试参数已相应修改。
尚待冻结后的独立 fresh 测试与全量证据审查，因此不以以上源码判断替代执行验证。

## 中间态负结果

首个定向命令在执行 `python -m unittest discover -s tests -p test_phase_context.py` 时，由 `Manifest.load(ROOT)` 拒绝当前路由中间态：
`schema routing/phrase_classes: Additional properties are not allowed ('requested_action' was unexpected)`。
9 个测试执行、10 个 setup 错误；后续两个命令由于 `set -e` 未运行。
协调者确认 routing 实施者正同步现有 manifest schema 与 packaged mirror。此项暂记工作未冻结造成的中间态，不宣称它是最终产品缺陷。

执行环境：Python 3.12 仓库 `.venv`，所有已读规则后的 shell 均经真实 `rtk proxy`，未调用模型或外部 runtime。
