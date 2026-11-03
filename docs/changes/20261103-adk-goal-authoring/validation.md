# ADK源码归属与项目应用回执

2026-11-03。reviewer_independence=author-self-review。无commit/push/release、设备操作或原业务Goal重建；不把源码候选称为已发布运行资产。

## 已落实

- `adk-goal-authoring`注册在manifest、core profile、goal_authoring路由和when-applicable handoff；平台中立实现位于typed core `goal_plan.py`，合同使用`adk.goal-plan/v1`。
- CLI公开`goal plan-check/render/resume`；现有goal check/state-check不变。新测试已加入既有test_execution_policy.sh，后续CI会运行。
- gros_compile根AGENTS、README和GOAL-WORKFLOW已指向ADK实际入口；原合同仅schema迁移，56个父标识和12组原状态保持。实际调用plan-check/resume通过，仍不操作宿主Goal。

## 新鲜验证

- 合同/状态/Skill治理/关系37项通过；既有execution_policy包装测试19+22项通过（含重叠测试，不相加宣称独立用例数）。
- 正触发“生成Goal目标合同”命中新技能；“已有完整计划只需执行”被non-trigger排除。
- profile context footprint 5项通过；新增入口4457和support1864字节，仅对core及继承profile按精确增量更新source-growth ratchet，增长负例仍会失败。不是运行token预算放宽。
- skill content 464 checks通过；trigger matrix 4项、profile coherence、content architecture 755 checks、docs CLI alignment和diff-check通过。
- validate --quick通过：58 core skills、8 optional。strict仅保留OpenAI来源审查和MCP来源审查过期两项失败，未改日期求绿。
- claude-code/core导出22个skill，实际包含新技能及合同示例。Codex目标明确是external handoff，不支持直接export；首次直接export被拒绝后改按平台支持入口验证，没有绕过。

源Skill SHA256=dc207e6e84200e01ccb4981f1a1c395311d2b4a3bb0a922ae5b8bc2bee669a16；typed core SHA256=269076c4052c17a4c1c073df66cd505a30e44ee9fd4da40b5944a8acf0a37126。

## 正式运行态边界

当前Codex provider lock为canonical jiying2007/agent-dev-kit 8.1.1，commit=95997abb318144aa6433fb40af4b2f0f1f4ceee4，不含新增资产。导入器要求exact release artifact hash、provider提交、promotion证据、Sigstore验证及源集核验；缺失时必须停在NEEDS_REVIEW。

因此：ADK源码注册和gros_compile项目工作流应用已完成；Codex live的goal-authoring仍是原local/codex资产，没有另装一个假来源adk-goal-authoring。正式身份替换还未完成。先解决来源审查和确定提交/发布范围，再取得独立commit/push/release授权并走受管导入；正式切换后退役local重复实现，不维持双权威。

原业务Goal本轮实读仍usage_limited、tokens_used=44680832、token_budget=null。项目文件更新不代表原线程已加载；没有恢复、清零或改变验收。
