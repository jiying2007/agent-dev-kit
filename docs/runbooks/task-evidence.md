# 真实任务观测、工件验收与配对比较

本入口把已授权宿主的观测材料接入既有 `TraceRunFacts -> RunEvidence -> compare_effect_trials`。
它不启动模型、不执行观测包内命令、不联网、不安装 Skill，也不新增调度或统计引擎。
本地摘要核验只能证明所提供材料的一致性；身份、记录完整性、原生加载和历史真实性仍由调用方提供可信来源。
验收材料和报告都保留 `trust=caller-observed`、`evidence_scope=test-only`、`raw_content_stored=false`；
导入与比较报告另保留 `quality_evidence_eligible=false`、`release_authorized=false`。fixture 通过不证明模型执行收益。

## 三个入口与返回值

从仓库根目录使用 CPython 3.12 和既有 `scripts/devkit.sh eval`。

| 入口 | 作用 | 返回码 |
|---|---|---|
| `grade-task` | 按已冻结开发合同核对最终工件，生成独立验收材料 | passed=0；failed=1；invalid=2 |
| `import-task` | 校验一个只读观测包并生成现有 RunEvidence | imported=0；invalid=2；导入成功不表示任务成功 |
| `compare-task-trials` | 核对任务初始状态与分组，再调用现有配对统计器 | improved/non-inferior=0；regressed=1；invalid/inconclusive=2 |

`--summary-json` 会向标准输出打印报告。有 `--output` 时，常规输出保存在指定文件；
输入、路径或摘要校验失败的 `status=invalid` 返回经过脱敏的 JSON，且不覆盖输入或输出文件。
有效的比较输入也可能产生 `status=compared, verdict=invalid`（如记录了基础设施失败）；
这类完整诊断报告正常写入安全输出，返回2，不是输入解析失败。
`grade-task` 的相对输出路径按 `--workspace` 解析；另外两个入口按当前工作目录解析。
跨目录使用时建议传绝对输出路径。

## 1. 准备真实观测

宿主先冻结任务、初始工作区、目标 Skill、模型快照、工具权限、采样设置、预算、缓存条件和独立验收方法。
旧版/新版 ADK 的 exact commit、导出 bundle 与既有 release contract 一起保留在原始证据中；
不得把任意不同 bundle digest 当成已证明的版本对照或 no-skill 对照。

每次运行使用独立目录。`observation.json` 采用 `adk-task-observation/v1`，只接受以下顶层字段：

| 字段 | 内容与要求 |
|---|---|
| `schema_version` | 固定为 `adk-task-observation/v1` |
| `provenance` | 真实记录为 `recorded-task`；测试生成材料为 `synthetic-fixture`，两者不可混合 |
| `run` | 运行、任务、执行者身份；任务源码、bundle、runtime/model/prompt版本；编排模式；起止时间；隐私状态 |
| `input_snapshot` | 原始任务输入的有界文件引用 |
| `workspace_snapshot` | 运行开始前完整工作区快照或清单的有界文件引用；不要用最终状态替代 |
| `events` | 有完整性声明的事件账本引用 |
| `acceptance` | 独立验收材料引用 |
| `artifacts` | 最终产物引用列表，须与验收记录完全一致 |
| `skill_exposure` | `target_skill`、分配的 `expected=loaded/absent` 和目标 Skill 内容引用 |

所有文件引用是 `{path, sha256}`，路径相对本观测包目录，摘要为原始文件字节的 SHA-256。
不接受路径逃逸、软链接、特殊文件、重复字段、非有限数或摘要不符。
当前单文件上限4MiB、单包总读取上限32MiB、最多128个读取文件、4096个事件；超限应缩小或分拆真实任务范围，不能截断账本假装完整。
安全导入依赖描述符相对读取、`O_NOFOLLOW` 与 `O_DIRECTORY`；平台缺少这些能力时拒绝导入，不降级为跟随链接的读取。

`run` 的封闭字段为 `run_id / task_id / executor_id / source_sha / asset_bundle_sha256 /
runtime_target / runtime_version / model_version / prompt_version / orchestration_mode /
started_at / finished_at / privacy_status`。
**`source_sha` 指被测任务初始仓库的 commit，两侧必须一致。** ADK/Skill 的干预版本由两侧
`asset_bundle_sha256` 及实际 Skill 内容摘要区分；其对应的 ADK commit 由冻结的导出/发布材料证明。
两种源码身份不可混用。快照内容的完整性仍由采集宿主负责，导入器不凭摘要认证历史工作区。

## 2. 保留完整过程和计量

事件账本包含 `schema_version=adk-task-events/v1`、`run_id`、`coverage` 和有序 `events`。
每个事件有唯一 `event_id`、从1连续递增的 `seq` 和限定 `kind`。
覆盖声明 `tools / human_interventions / skill_loads / attempts / handoffs / guardrails` 必须都为 true；
这些计数未知时拒绝完整导入，不补成0。`model_calls=false` 时用量和费用明确不可用。

支持 attempt、skill-load、tool-call、model-call、human-intervention、handoff、guardrail、termination。
工具和模型事件必须归属已记录的 attempt；实际 Skill 加载含内容摘要和 primary 标记。
原始账本保留所有失败、重试和子任务；模型事件按唯一 `call_id` 和 `accounting=exclusive-call` 记账，
不把父级合计与子调用重复相加。

模型调用的 Token 为 input、cached_input、output；cached_input 已包含在 input 中，不能再次加到总输入。
只聚合 runtime/provider 实际报告的值。任一调用缺测、估算或采集不完整，则对应整次运行指标不可用；
字符数、输出长度和估算价格不能冒充 Token 或账单。费用币种必须一致。
first-pass success 需要最终成功、单 attempt、无人为干预且无错误路由；它不等于“命令返回0”。

固定任务预算耗尽、执行循环或重试耗尽属于有效失败，通过 termination 保留 timeout 证据和全部用量。
基础设施采集故障另外记录为 invalid/incomplete；不得为改善候选结果而单侧重跑或删掉失败。
原因不明保持未知。实际未加载预期 Skill 保留在原分组并标记错误路由；
是否完成任务仍由独立产物验收判断，不按加载成功与否选择性筛选样本。

## 3. 独立验收最终产物

八类公开开发任务位于 [开发基准说明](../../tests/fixtures/skill_execution_tasks/README.md)。
owner 将选定任务的 `initial/` 复制到观测包的 `work/`，执行者只获得任务描述和工作区；
`case.json` 与原输入由验收者保管在执行者写权限之外。
这些公开答案只用于开发，不能成为新的独立最终 holdout。

执行完成后，例如验收定向 ADR 修改：

```bash
bash scripts/devkit.sh eval grade-task \
  --case tests/fixtures/skill_execution_tasks/targeted-document-edit/case.json \
  --workspace /absolute/path/to/recorded-run \
  --output acceptance.json \
  --run-id adr-trial-1 --executor-id task-executor --grader-id artifact-grader \
  --summary-json
```

生成 `acceptance.json` 与 `acceptance.json.checks.json`。验收要求完整 JSON 内容、原文件字节保持或唯一授权文本替换，
并检查整个 `work/` 的缺失/额外文件；不执行候选代码或自定义命令。
执行者与验收者身份必须不同，但身份差异本身不是独立性认证。
真实任务也可由现有受信任验收程序产生同一 `adk-task-acceptance/v1`：
`schema_version=adk-task-acceptance/v1`、run/task/executor/grader 身份、status、artifacts、checks、guardrails、trust、evidence_scope 和
`raw_content_stored=false` 全部必需，不额外加入导入报告的 authority 字段。
开发 grader 只产生 passed/failed；blocked/not-run 是外部验收可以提供的状态。

最终产物正确不能证明中间没有越权或重复发布。artifact guardrail 与事件账本的 process guardrail 分别保留；
过程失败不能被最终文件通过掩盖。失败、blocked 和 not-run 验收都保留原始记录。
不自动把一般代码的语义等价解法压入本开发套件的精确文本合同；真实项目应使用预先冻结的项目验收。

## 4. 导入单次记录

```bash
bash scripts/devkit.sh eval import-task \
  --input /absolute/path/to/recorded-run/observation.json \
  --output /absolute/path/to/reports/run-1.json \
  --summary-json
```

导入结果的 `run_evidence` 是现有组合协议，包含任务结果、验证引用、用量和过程事实。
原始正文不会复制到摘要。输出写入前验证整个读取集合，不能覆盖 observation、事件、验收、产物或它们的别名。
安全文件操作面向调用方拥有且稳定的目录，不宣称对抗恶意并发写入的操作系统沙箱能力。

**单份导入不证明有效配对。** 它标记 `pairing_authority=none-single-observation`。
直接把两个 run 拼进通用 `compare-trials`，不能证明它们具有相同初始工作区或干预条件。
任务比较应走下一步的专用前置核查。

## 5. 冻结并比较完整分组

`schema_version=adk-task-trials/v1` 复用已有 `effect-trials-v1` 的 `plan`，另包含以下字段：

- `task_bindings`：每个 task 的 input/workspace SHA-256 及任务初始 `source_sha`。
- `conditions.baseline[task_id]` 与 `conditions.candidate[task_id]`：该任务的 target_skill、expected 和 content_sha256；不同任务可对应不同 Skill。
- `grader_id` 和 `provenance`：固定验收者和记录类别。
- `trials`：trial_id、infrastructure_status，以及 baseline/candidate 的 observation 路径与摘要列表。

构造计划时用 `agent_dev_kit.task_trials.task_trial_controls_ref(document)` 写入
`plan.controls.dataset_ref`。它同时绑定任务快照、分组条件、grader 和 provenance；
其余模型、工具、采样、上下文、预算、缓存、样本与统计规则继续使用原 plan 协议。
注册时间和真实性仍须原始外部记录支撑，重新计算摘要不能把事后计划变成预注册。

```bash
bash scripts/devkit.sh eval compare-task-trials \
  --input /absolute/path/to/campaign/task-trials.json \
  --output /absolute/path/to/reports/comparison.json \
  --summary-json
```

入口逐次导入，核对实际输入/初始状态/任务源码、分配的 Skill 内容和验收者，再交给唯一既有统计器。
错误来源版本、工作区漂移、no-skill 侧实际加载目标 Skill、不同记录类别混用等拒绝比较。
缺少计划样本会拒绝比较，不补造失败或成功。已观测失败与未触发保留在完整分母；
统计置信区间、配对规则与 non-inferiority 判定继续由原比较器负责。
当前有界入口最多读取120份观测及64MiB输入；不得为绕过边界而只保留通过样本。

champion/challenger 比较版本增量；no-skill/with-skill 是另一个消融问题，需单独冻结真实暴露条件。
公开8任务×2分组×2次重复可以作为先导批次示例；不是每个 Skill 的强制模板，也不足以承诺小幅或广泛收益。
候选冻结后再由独立评测方产生未参与优化的任务与 grader；如果用留出集改了技能，需重新建立未见留出集。

## 验证和无法获得真实观测时的恢复

```bash
bash tests/test_run_evidence.sh
bash tests/test_skill_content.sh
```

合成包生成器分别为 `tests/test_task_evidence.py::synthetic_package` 与
`tests/test_task_trials.py::synthetic_task_trials`，只能验证输入协议和确定性机制，不能改标 recorded-task。
原未执行方法方案仍在 `tests/fixtures/skill_method_ab_prereg.json`，保留历史候选、空结果与作者曝光限制。

缺少允许宿主、完整事件、独立验收或使用量时，状态保持 `evidence-blocked/not-measured`。
仅使用量缺测时仍可导入可靠任务结果，Token/cost 明确 unavailable；若这些是必要主指标，比较会 inconclusive，
不一概否定已经得到的产物证据。
保留已冻结源码与任务、缺失材料和上述三个恢复命令；拿到真实材料后从导入继续。
不重复请求已有执行授权，不新增定时巡检，不调用用户禁止的 Codex/ChatGPT Work 额度，
也不以 discovery/load/trigger 的烟测替代真正任务完成与成本比较。
