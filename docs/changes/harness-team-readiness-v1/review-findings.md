# 独立审查发现：harness-team-readiness-v1

- Review Scope: readiness typed core、CLI、manifest、fixtures/tests、capability 接入、legacy migration 与 Harness 文档。
- Requirement Baseline: `proposal.md`、`design.md`、七维无权重 evidence projection、默认 report-only、敏感值不回显、有限扫描。
- Verification Baseline: 审查启动时 Harness 定向测试、capability health、CLI docs alignment、format、file mode 与 strict validate 已分别取得通过结果；审查修复闭环后 full regression 53/53 通过，最终命令证据见 `verification-evidence.md`。

## Findings

| ID | Severity | File | Evidence | Required Action | Status |
|---|---|---|---|---|---|
| HR-001 | major | `src/agent_dev_kit/readiness.py:318` | `_safe_secret_reference` 只要包含 `${` 就判安全；实测 `hardcoded-${TOKEN}` 返回 True。敏感 key 的 list/number/object value 也因只检查 string 而被漏过。 | 只接受完整环境/secret reference 语法；非空非字符串敏感值一律 blocked；增加混合值与非字符串回归。 | fixed |
| HR-002 | major | `src/agent_dev_kit/readiness.py:398` | 合同限制总文件和单文件大小，但 MCP config 数量、JSON 遍历和 blockers 无上限；最坏可读取 5000 个 1 MiB 配置并生成巨大报告。 | 增加 `max_mcp_configs` 与 `max_blockers_per_dimension`；超限必须保持 non-pass 并输出截断问题码。 | fixed |
| HR-003 | major | `src/agent_dev_kit/readiness.py:491` | `tests/` 下任意文件都算测试；任意路径只要文件名含 recovery/freshness 关键词就算机械证据，template 或说明文档可让维度误报 pass。 | 排除 template/example 证据；测试要求可识别测试文件；recovery 限定 runbook/script；freshness 限定 script/test/CI/Makefile 等机械入口，并增加诱骗 fixture。 | fixed |
| HR-004 | major | `src/agent_dev_kit/readiness.py:27` | `load_readiness_contract` 未验证 `contract_version`、dimension title/next_action、MCP 字段与新预算；后续直接索引，用户传入结构不完整的 `--contract` 可能抛未捕获 KeyError；复审进一步检查了深嵌套 JSON 的 `RecursionError`。 | 在 load 阶段完整验证所有运行期必需字段，只抛 `ReadinessContractError`，增加 malformed/deep contract 回归。 | fixed |
| HR-005 | major | `scripts/quality-gates.sh:21` | 旧入口从旧质量目录语义改为 canonical checker；路径保留但行为不兼容，而 `proposal.md` 将变更声明为非 breaking。 | 将 proposal/design 明确改为有迁移说明的行为 breaking change，保留调用点复核和回退；文档不得声称无兼容影响。 | fixed |
| HR-006 | minor | `src/agent_dev_kit/readiness.py:152` | metadata 路径存在但因超预算/不可读时，与文件不存在同样返回空 metadata，最终多为 partial 而不是明确 invalid metadata。 | 区分 absent 与 unreadable，后者产生 `unreadable_readiness_metadata` 并至少 needs-review。 | fixed |
| HR-007 | major | `src/agent_dev_kit/readiness.py` | 权限证据只做关键词子串匹配；`not read-only / no approval / hardcodes credentials` 的反面说明仍让工具维度返回 pass。 | 使用结构化 metadata 作为 gate 证据；启发式文本至少拒绝否定语境，并增加诱骗 fixture。 | fixed |
| HR-008 | major | `src/agent_dev_kit/readiness.py` | `last_verified_at` 只校验 ISO 语法，未来日期和任意陈旧日期都被接受，不能证明 evidence freshness。 | 在合同声明最大 age 和未来偏差，输出 future/stale blocker，并补边界测试。 | fixed |
| HR-009 | major | `src/agent_dev_kit/readiness.py`、`src/agent_dev_kit/cli.py` | `--gate --as-of <历史日期>` 可冻结评估时钟，使过期 metadata 长期保持 pass。 | `--as-of` 仅允许 report-only；gate 强制使用当天，增加历史日期拒绝回归。 | fixed |
| HR-010 | major | `src/agent_dev_kit/readiness.py` | 任意嵌套目录的 `OWNERS` 都被当作仓库级 ownership，模块局部 owner 可使 freshness 维度假通过。 | 仅接受根 OWNERS/CODEOWNERS 与 GitHub 约定 CODEOWNERS 路径，增加嵌套诱骗负例。 | fixed |

## False Positives

- “ADK 自身 readiness 只有 partial”不是本实现缺陷：基线明确证明 270 行 AGENTS、owner/验证时间与 CODEOWNERS 是当前仓真实 evidence gap。
- “没有 MCP”不是缺陷：合同按设计输出 `not-applicable`，不应为了完整度接入外部系统。

## Out-of-scope Suggestions

- 拆分 ADK 根 `AGENTS.md` 与新增仓库 ownership 证据已由独立 `adk-self-readiness-ownership` change 承接；多 owner 运营和远程 identity 仍不在本 change 内。
- 原公众号 URL intake 与 30 天多仓试点继续保持开放证据，不影响 source/test 层修复。

## Fix Plan

1. 收紧 secret reference 与敏感类型判定，加入脱敏负向测试。
2. 完整验证 contract 并增加 MCP/blocker 预算。
3. 收紧 material evidence 规则，加入 template/README 诱骗 fixture。
4. 修正 breaking-change 声明和迁移边界。
5. 禁止 gate 覆盖评估日期，并限制仓库级 owner 证据位置。
6. 重跑原发现定向测试、strict/quick/full gate 后复审。

## Re-review Result

- 第一轮复审：HR-001、HR-004、HR-005、HR-006 已由定向测试和代码证据闭环。
- 第二轮复审：HR-002 已在 config、permission docs、blocker 收集和最终报告四层限界；HR-003 已排除 template MCP/permission/ownership 与伪测试/伪恢复/纯说明证据。
- 深嵌套 contract、混合 secret placeholder、非字符串 secret、malformed contract、evidence decoy、MCP config/blocker 超限均有负向回归。
- 第三轮复审：HR-007/HR-008 的结构化权限和 future/stale 边界已闭环；HR-009 的历史时钟与 HR-010 的嵌套 OWNERS 诱骗均稳定拒绝。
- 复审验证：`rtk agent-dev-kit/tests/test_harness_readiness.sh`、`rtk agent-dev-kit/scripts/check-format.sh`、`rtk agent-dev-kit/scripts/devkit.sh validate --strict`、`rtk git -C agent-dev-kit diff --check` 均通过。

## 2026-07-18 Final Decision

- 原 pass 曾因 HR-007/HR-008 反例被正确撤销；本轮又发现并修复 HR-009/HR-010。
- blocker=0, major=0, minor=0, question=0。
- 本地 source/test change 可恢复 `pass`；field evidence 仍为 `not-verified`，不构成 terminal/runtime 放行。
