# 设计说明：intent-boundary-governance-v2

## 总体结构

本变更不增加新的运行角色或流程入口，只把现有自然语言边界提升为四个相互衔接的声明式合同：

```text
skill_invocation
  -> direct target adapter / Codex external handoff
  -> discovery only, never grants permission

task-package-v2
  -> decision | research | prototype | implementation
  -> permission + exit gate + handoff

architecture scope
  -> requested scope | current diff | recent hotspots | first-order dependencies
  -> explicit expansion reason

prototype_evidence
  -> question + provenance + result + retention + cleanup
```

统一原则：调用决定“是否发现 Skill”，工作项合同决定“允许做什么”，target/permission policy 决定“运行时能做什么”；三者不得互相替代。

## 1. Skill invocation SSOT

### Manifest 合同

`manifest.json` 新增必填顶层对象：

```json
{
  "skill_invocation": {
    "default_mode": "implicit",
    "overrides": {}
  }
}
```

- `default_mode` 只允许 `implicit|explicit-only`。
- `overrides` key 必须引用已登记 core/optional Skill；未知、Agent 或 Workflow 名称失败。
- 初始没有 production override：ADK 当前所有 Skill 仍以 intent routing 为主，不因吸收外部命名体系改变既有触发行为。
- 新增 override 必须同时增加正/反路由 fixture、owner rationale 和目标适配证据。
- `Manifest.skill_invocation_mode(asset)` 是编译器唯一读取入口；adapter 不自行推断 Skill 名称或 trigger。

### 通用 reproducibility 合同

`manifests/skill_reproducibility_contracts.json` 增加 `cross-harness-skill-invocation-v1`：

- 必需字段：`skill_name`、`invocation_mode`、`target`、`metadata_path`、`explicit_invocation_evidence`、`permission_boundary`。
- Codex 映射：
  - `implicit`：官方嵌套 `interface` metadata，省略 `policy`。
  - `explicit-only`：增加 `policy.allow_implicit_invocation=false`。
- Claude 映射：
  - `implicit`：不生成 `disable-model-invocation`。
  - `explicit-only`：生成 `disable-model-invocation: true`。
- 明确拒绝顶层 Codex `display_name/short_description`、显式 `allow_implicit_invocation=true`、target adapter 自行猜测和“可调用即已授权”。

### Direct target contract

`target-contract.schema.json` 与三个 target contract 增加：

```json
{
  "skill_invocation": {
    "supported_modes": ["implicit"],
    "explicit_only_frontmatter": {}
  }
}
```

- Claude Code 当前合同支持两种 mode，并将 explicit-only 映射为 `disable-model-invocation: true`。
- Hermes Agent 与 OpenCode 没有本 change 已核验的等价字段，只声明支持 `implicit`；收到 explicit-only 时 fail closed，不做静默降级。
- Codex 不是 direct target；其 mapping 由 `~/codex` external handoff adapter 实现。

## 2. Task package v2

### 硬切字段

删除 `adk-task-package-schema-v1`，以 `adk-task-package-schema-v2` 取代。除既有字段外新增必填：

- `work_item_kind`：`decision|research|prototype|implementation`
- `question_to_resolve`：该票唯一要收敛的问题；implementation 填已接受的 spec/任务问题。
- `evidence_required`：进入 exit gate 前的原始证据要求。
- `implementation_permission`：`forbidden|approved`
- `exit_gate`：`owner-decision|evidence-reviewed|prototype-reviewed|implementation-verified`
- `handoff_target`：下一阶段 owner/Skill/Workflow；终态可为 `none`。
- `retention_decision`：`keep-final|archive-negative-result|delete-orphan|expire`

### 跨字段不变量

| kind | implementation_permission | exit_gate | 允许输出 |
|---|---|---|---|
| decision | forbidden | owner-decision | decision record、备选与理由 |
| research | forbidden | evidence-reviewed | cited evidence、negative result |
| prototype | forbidden | prototype-reviewed | prototype evidence，不是生产实现 |
| implementation | approved | implementation-verified | 代码/资产与验证证据 |

- 只有 `implementation` 可使用 `approved`。
- research 可以在 `adk-parallel-agent-governance` 准入后并行，但默认只读、data-only handoff。
- prototype 必须引用 `prototype_evidence`，不能仅以 branch 名或截图作为 provenance。
- 任一非 implementation 类型请求写产品代码时，结论固定为 `blocked/replan`。
- v1 输入不迁移、不补默认字段、不保留 reader。

### 消费方

- `adk-task-breakdown`：创建和校验 v2，先按问题/决策切分，再按实现模块切分。
- `adk-planning-execution-loop`：checkpoint 记录 kind、exit gate 和 handoff；research/prototype 完成后返回计划审查。
- `adk-parallel-agent-governance`：只有独立 research 票或已批准 implementation 票可并发；父控制面统一 truth commit。
- `templates/artifacts/task-breakdown-template.md`：每票独立字段，可存放于当前 change 的 `tasks/` 目录，并由索引汇总；不固定 `.scratch`。

## 3. Architecture hotspot/YAGNI scope

`architecture-planner` 增加确定性范围选择顺序：

1. 用户明确 scope。
2. 当前 diff/工作项声明的 target paths。
3. `base_ref..HEAD` 的近期变更热点。
4. 上述触点的一阶 contract/dependency。

默认 `broad_scan=false`。只有发现 shared contract、循环依赖、跨模块故障域、安全边界或用户显式要求时才扩域，并记录：

- `base_ref`
- `history_window`
- `selected_hotspots`
- `first_order_dependencies`
- `broad_scan`
- `expansion_reason`

不引入 HTML/CDN/browser 报告前提；Markdown/JSON evidence 是默认输出。

## 4. Prototype evidence

`structured_output_contracts.json` 新增 `adk-prototype-evidence-schema-v1`，`schema_target=prototype_evidence`，必需字段：

- `question`
- `base_commit`
- `scope`
- `artifact_path`
- `artifact_sha256`
- `runtime_assumptions`
- `observed_result`
- `decision_supported`
- `verification_command`
- `verification_exit_code`
- `retention_decision`
- `expires_at`
- `cleanup_owner`
- `rollback_anchor`
- `active_references_absent`

规则：

- `base_commit` 必须是 7–64 位小写 hex revision；artifact path 必须为仓内相对路径，不得穿越、使用绝对路径或进入 `.git/`。
- 默认使用 change/evidence 目录中的 data artifact；不得写 `.git/`。
- branch/worktree 不是默认保存方式；确需可运行历史时先走 `adk-worktree-governance`，记录 base、expiry、cleanup owner 和 rollback。
- `retention_decision=expire` 时必须有未来 `expires_at`；`delete-orphan` 只在 `active_references_absent=true` 时成立。
- 原型结果只能支持/反驳决策，不能替代 production test 或 implementation verification。

## 5. Codex external handoff

`~/codex` 是 Codex 运行资产源码，`~/.codex` 只由 build/plan/apply 生成：

1. 分类并保留 `~/codex` 既有 dirty，不覆盖无关变更。
2. 将所有 managed Skill metadata 硬切到：

   ```yaml
   interface:
     display_name: "..."
     short_description: "..."
   ```

3. 只有 manifest override 为 `explicit-only` 时生成：

   ```yaml
   policy:
     allow_implicit_invocation: false
   ```

4. `check_skills.py`/等价门禁解析 YAML，拒绝 legacy 顶层键、显式 true、未知字段类型和 manifest mode drift。
5. 不保留一次性转换器、兼容 reader 或双格式 fixture；迁移通过一次受审查的机械 patch 完成。

## 6. 测试与负结果

### ADK deterministic tests

- manifest 缺 `skill_invocation`、未知 override、非法 mode 均失败。
- Claude explicit-only fixture 生成正确 frontmatter；OpenCode/Hermes explicit-only fixture fail closed。
- active tree 的 v1 schema 标识零命中。
- task v2 必需字段与四种 cross-field rule 被机械检查。
- research/prototype + `approved` 是负例。
- architecture scope 和 prototype evidence marker 完整。
- token budget、manifest sync、target export、strict/full regression 不回退。

### Codex tests

- managed `openai.yaml` 全量 YAML parse。
- 顶层 legacy metadata、explicit true、非布尔 policy 和 mode drift 负例。
- build 输出与 source metadata 数量/hash 对齐。
- source-to-live plan/dry-run 不出现意外删除或无关覆盖。

## 7. 版本、迁移和回退

- ADK product：`3.1.0-rc.4 -> 3.1.0-rc.5`。
- 修改 Skill 各自 bump minor：task breakdown、parallel governance、planning loop。
- 新增 migration doc，明确 task schema v1 和 legacy Codex metadata 已删除。
- 回退锚点：ADK `bffcd93`；root `e7b92eff2cf426ca86614e0a67c59232151bcda9`；Codex 使用 apply 前备份/已提交 source anchor。
- 回退只整体撤销 RC5/source adapter change；不得恢复兼容层。
