# T2 实施与定向验证

实施者：`ai/root/audit_core`。本记录对应角色从只读审查切换为 T2 实施，
不构成本次修改的独立审查。需求、设计由协调者制定，见 ADK 仓库
`docs/changes/20261117-routing-context-integrity/`。没有 commit/push。

## 改动

- 四个既有 LRU 保留 maxsize=8 / 512；解析缓存键改为读取到的 raw bytes，
  phase/relationship schema 字节也在键中。
- Phase/relationship 输出摘要来自同次读取并解析的 raw bytes；没有二次读取算摘要。
- 原 contract/schema 缺失检查保留；坏 UTF-8 和读取失败统一为 ManifestError。
  Frontmatter 对缺失文件、不可读/坏 UTF-8、缺失/未闭合/非法 YAML 分别保持明确错误。
- Campaign 每个 attempt 的 actual_safe 要求 bool；实际 runtime error 仍可用 None。
  elapsed/cost 排除 bool 并要求有限非负数；非 Claude 的 cost=None 保持原约束。
- 最后 attempt 与 final 使用已有 canonical digest 比较，避免 Python dict 相等把
  `False` 与 `0` 当同一快照；没有改变结果字段或增加新的持久化格式。

修改文件（8）：

1. `src/agent_dev_kit/phase_context.py`
2. `src/agent_dev_kit/skill_relationships.py`
3. `src/agent_dev_kit/matcher.py`
4. `src/agent_dev_kit/_matcher_kernel.py`（仅 frontmatter loader）
5. `src/agent_dev_kit/campaign_analysis.py`
6. `tests/test_phase_context.py`
7. `tests/test_skill_relationships.py`
8. `tests/test_effect_campaign_materializer.py`

## 证据

调用点检索覆盖 src/tests/tools/scripts 中的 `_load_contract` 和
`_frontmatter_cached`；两个直接使用私有 loader 的既有 schema 测试随签名更新。
`knowledge/L2-domain/lessons.md` 不存在，未虚构经验命中。

新增 14 个 test methods（其中若干含 subTests）；原有测试断言保留。

- `tests-red.log`：第一次 12 方法的基线 RED，19 failure subcases / 3 errors。
  三个 error 是原实现对坏 UTF-8 抛出 UnicodeDecodeError 而非 ManifestError。
- `tests-green.log`：首轮产品修复后 33 tests PASS。
- `tests-final-alias-red.log`：补充 final 类型别名反例为 1 failure / 2 tests，
  同时 frontmatter 的坏 UTF-8 / 删除后读取失败检查通过。
- `tests-final-green.log`：最终对应三个测试模块 **35 tests PASS，2.299 s**。
- `ruff-final-green.log`：8 个修改文件的 Ruff PASS。
- `git diff --check`：实际执行返回 0。

覆盖：contract/schema 同 size+mtime 内容更新；valid→valid 的选择结果/关系刷新；
invalid 拒绝；digest 与实际字节一致；不变内容 cache 命中与固定 LRU 上限；
错误安全类型/boolean 数字/NaN/Inf 拒绝；合法零值、False、安全 None 和 cost None；
真实 materializer 的三项错误输入拒绝；final 与 last attempt 类型一致性。

第一次 Ruff 报 matcher 中废弃 Path import，以及既有测试文件未使用的 copy import；
两者已删除，最终 Ruff 通过。第一次添加测试时错误地将既有 tamper method 的后半段
接到新方法后，产品修改前已恢复原方法范围；没有删除其 alias/window/missing 断言。

## 仍由集成承担

完整回归、固定路由、预算、benchmark、独立 review、发布与 Root 接入由协调者
完成。本任务不重复性能实验，不宣称 Token、费用、真实模型或设备效果。

## IR-1 独立审查后补充

独立 reviewer 的原始探针保留于 `../independent-review/`。它确认巨大 JSON 整数
`10**400` 在耗时转换时抛出未处理的 OverflowError，且两个各 1e308 的有限耗时
相加后成为 Infinity，原校验仍返回 passed=true / latency_complete=true。

只修改 campaign_analysis 与对应 materializer 测试完成补充：使用同模块
`_finite_nonnegative` 将转换错误归入 ManifestError，保留实际转换值，逐项及合计
均检查有限非负。费用采用相同转换/合计校验；对原输入字典不作修改。

- 新增 3 个方法，`tests-numeric-boundary-red.log` 保存 2 failure / 1 error 的原 RED。
- `tests-numeric-boundary-green.log`：materializer 全部 **11 tests PASS，1.828 s**。
- 费用 2×1e308 的聚合反例同样先红后绿；该 typed-validator 探针使用显式极大
  per-call 参数，仅验证数值边界，并未修改生产 contract 的费用上限。
- `campaign-number-probes-after-fix.json`：复跑原独立脚本，正常有限值接受，其余
  boolean/NaN/Inf/巨大整数/总和 overflow 均为 ManifestError。
- `ruff-numeric-boundary-green.log` 和 `git diff --check` 均通过。

已通知协调者和独立 reviewer 修复待复验；以上是实施者观察，独立裁决仍由 reviewer
给出。第一次“35 tests”结果保留为当时的准确结果，不把新增测试计入旧运行。
