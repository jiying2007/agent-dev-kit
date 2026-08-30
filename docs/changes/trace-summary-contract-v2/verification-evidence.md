# 验证证据：trace-summary-contract-v2

验证日期：2026-08-30。执行环境默认 `Python 3.8.10`，因此 Python 结果仅属于 development evidence，
不能作为 Python 3.11/3.12 release evidence。

## Evidence Index

| Command | Exit | Result | Layer | Evidence |
|---|---:|---|---|---|
| `rtk tests/test_trace_summary.sh` | 0 | 12 tests passed；含 typed emitter、per-run、默认 unavailable、隐私和不一致事实负例 | contract/unit | command output |
| `rtk tests/test_runtime_boundary.sh` | 0 | platform-neutral boundary passed | security | command output |
| `rtk tests/test_agent_ecosystem_standards.sh` | 0 | ecosystem standards passed | integration | command output |
| `rtk tests/test_official_docs_governance.sh` | 0 | trace governance passed | governance | command output |
| `rtk tests/test_skill_sop_quality.sh` | 0 | skill SOP quality passed | regression | command output |
| `rtk tests/test_target_contracts.sh` | 0 | v1 target compatibility passed | compatibility | command output |
| `rtk tests/run_all.sh --quick --fail-fast` | 0 | 28/28 passed | aggregate | command output |
| `rtk tests/test_format.sh` | 0 | format passed | lint fallback | command output |
| `rtk tests/test_file_modes.sh` | 0 | file modes passed | packaging | command output |
| `rtk scripts/devkit.sh validate --strict` | 0 | strict validation passed; development-only warning | validation | command output |
| `rtk git diff --check` | 0 | no whitespace errors | source | command output |
| `rtk ruff check ...` | unavailable | ruff executable not installed | lint | `negative-results.md` |

## Completion Guard

- build：not-applicable；本变更不生成 runtime/build 产物。
- lint：pass-with-fallback；仓库 format、120 列扫描和 diff check 通过，ruff 明确 unavailable。
- test：pass；本轮 emitter 定向 12/12；既有 contract 基线 quick 28/28，最终聚合由 umbrella change 复验。
- smoke：pass；runtime boundary、official governance、target compatibility 通过。
- security：pass；raw prompt/message/tool payload、未知字段、raw-content flag 负例均 fail-closed。
- release：not-applicable；没有 target promotion、安装、发布或 live 写入。
- verifier：实现子 Agent 自检；主 Agent 仍负责最终交叉审查和全量集成门禁。

## Replayable Evidence Bundle

- input snapshot：`requirements.md`、`manifests/trace_eval_contracts.json` 的当前 working-tree 版本。
- environment snapshot：Linux workspace；默认 Python 3.8.10，不受支持，结果为 development-only。
- tool transcript digest：上表命令及退出码；不保存 raw session/tool payload。
- expected assertions：schema/meta-schema 有效；类型/关系/隐私负例 fail-closed；v1 引用保持；每次显式
  emitter 调用只输出一个 run summary；缺 token/cost/outcome 时只输出带 reason 的 `not-available`。
- sensitive-data review：fixture 只含合成标识和度量，不含 prompt、message、tool payload 或凭证。
- non-replayable reason：无；命令均可在仓库根目录复跑，但 release evidence 需 Python 3.11/3.12。
- artifact hashes：
  - manifest `4fd903d61b6f493340d8ebd0ce59d9bc29bda8f55e9ef9fb8c5bfe1099645aa6`
  - schema `2c59681ed39436c7a00f1b0d97c1292af67e60e9f1cdafbbed3cf5f059d56073`
  - validator/emitter `3c1aba96d1076852af700f52c5c0c3dfee6a1124410e365b75db83934b64c2cf`
  - Python tests `a414998a7934eb63135ebad1c2377d44d49eb03f67b1b172ea7954559adde74c`
  - shell test `aea74e97f12f87ade244d9c650a28dc19d21ecd1b49f03d136e276d5158edc7b`

## Compatibility, Architecture, and Rollback

- breaking decision：non-breaking opt-in；v1、target 和 OTel adapter 引用保持不变。
- architecture：新增控制面 schema/validator 和 explicit-call emitter library；不实现 scheduler、外部 exporter、
  自动 runtime instrumentation 或 native target integration。
- permissions：未放宽 sandbox、approval、MCP、Hook、Plugin 或外部写权限。
- UI/Appshots：not-applicable。
- runner/CLI：not-applicable；没有修改 CLI 或 runtime adapter。
- trace eval regression：本变更自身是 trace evidence contract；未修改 prompt、routing 或 completion policy，
  因此 dataset promotion contract not-applicable。
- rollback：删除 v2 manifest 条目、schema、validator、测试和 change 目录；v1 消费者不受影响。

## Codify Decision

- delivery_goal：提供严格、隐私有界且不虚报自动 runtime 集成的 trace summary v2 per-run emitter。
- reusable_pattern：immutable typed facts + explicit unavailable envelope + 封闭 JSON Schema + 确定性跨字段
  validator + 敏感字段递归拒绝。
- affected_asset：trace/eval contract、typed core、test aggregate。
- promotion_candidate：false。
- next_task_friction_reduced：true；后续 runtime adapter 可复用单一 typed emitter/schema/validator。
- reduced_by：消除各 adapter 自定义 token/cost/outcome/privacy 结构和关系检查。
- reduction_evidence：定向测试及 quick 聚合门禁已固定公共行为。
- do_not_promote_reason：explicit-call emitter 已可用，但 automatic runtime/native target conformance 尚不可用，
  需 owner review 后另行启用。
- owner_review：pending main Agent/owner。
- rollback_path：按上一节删除 opt-in v2 资产，保留 v1。
- verification_evidence：本文件 Evidence Index。
