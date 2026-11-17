# 三份只读诊断任务交接：现有 Skill 消费结果

## 范围与证据边界

本结果仅依据协调者给出的 A/B/C 题设，以及实际读取的以下两个 Skill：

- `/workspace/scratch/d417066aafa8/agent-dev-kit/skills/adk-context-engineering/SKILL.md`
- `/workspace/scratch/d417066aafa8/agent-dev-kit/skills/adk-context-compress-handoff/SKILL.md`

没有读取仓库其他审查、设计或实现记录，没有访问题设中的诊断 Skill、reference 或日志文件，没有修改产品源码、访问设备或运行模型 CLI。下文中的诊断 Skill 路径、内容身份、事实、阻塞和下一动作均为题设变量；未给出的具体值不作补造。所有“重读”“执行”均为情境中的后续建议，不表示本次已执行。

两个实际读取的 Skill 分别在 `Context Policy / Workflow 3–6` 与 `Workflow 3–5` 规定：保存必要 Skill 的来源、内容身份、必要 refs 和正文状态；恢复先核目标与权限；只有同来源、同内容、完整正文仍在当前上下文时才去重；正文摘要化、丢失，或来源、内容变化时按需重读；历史“已加载”不是有效性证明。两个 Skill 对缺证据门禁分别使用 `needs-evidence` 和 `needs-fix`，本结果并列记录，避免混淆。

## 判定总表

| 情境 | 当前有效性判定 | 最小恢复动作 | 此时门禁 |
|---|---|---|---|
| A | 题设已满足同来源、同内容、完整正文和必要 refs 均仍在上下文 | 复用现有正文和 refs，直接衔接既定下一只读动作 | 恢复核对可为 `pass`；不等于诊断完成 |
| B | 摘要中的“此前已加载”不能替代缺失正文 | 读取已知路径的诊断 Skill 与当前任务必需 refs，记录本次实际内容身份及正文状态 | 补回并核对前为 `needs-evidence` / `needs-fix`；完成后才可改为 `pass` |
| C | 名称相同不能抵消来源路径和内容身份已变化 | 从当前可信目录指向的新来源加载正文，核对新正文要求的必要 refs；旧正文不再作为当前执行依据 | 新正文及必要内容核对前为 `needs-evidence` / `needs-fix`；完成后才可改为 `pass` |

## A：继续同一只读诊断任务，正文与身份均保持有效

### 最小动作

1. 在恢复记录中引用题设已确认的目标、权限、来源与内容身份一致性，以及正文和必要 refs 完整保留的状态。无需为了证明“曾加载”再读取一次 Skill，也无需重载完整历史。
2. 使用当前完整正文与已有必要 refs，执行原任务已经确定的下一项只读诊断动作。具体动作未提供，不能替换成新发明的日志命令或扩展任务。

第一条建议命令：沿用原任务已确定的下一条只读命令；题设未给出该命令，本交接仅保留其原值，不编造可执行命令。这里没有新增的 Skill 重读命令。

### 应保留的最小交接信息

- `Latest Goal / Phase`：同一只读诊断的原目标及当前阶段。
- `Confirmed Facts`：继续决策所需的已确认事实，保留其来源、时间或 raw evidence 指针；假设另列。
- `State / Blockers`：已完成项、未决项、阻塞，以及仍影响后续行动的残余风险；如存在诊断对象或候选身份，保留其精确身份。
- `Scope / Permission`：原有只读范围与权限，不增加设备访问、模型 CLI 或写操作。
- `Active Skills`：名称作为标签；精确来源路径；可信目录确认未变化的内容身份（可核版本或 hash，具体值未给出）；必要 refs 及其可追溯指针；正文状态 `intact`。记录“正文仍在当前上下文”，不能只写“曾加载”。
- `Evidence / Fallback`：必要日志或原始证据指针、验证结果，以及何时需要重新取证。若后续发现正文缺失、身份变化或证据失效，再按缺项恢复；不要预先重复全部读取。
- `Next Action`：原任务已确定的第一项下一只读动作及成功判据。
- `Recovery check / Gate Result`：`pass`，依据为本情境题设；该标记只说明恢复条件满足，不证明诊断结论或任务完成。
- `Excluded Context`：不再适用的 Skill、过期目标、失败假设和无关历史；只在实际存在时列出，不虚构条目。

### 可粘贴恢复提示

> 继续原只读诊断。目标与权限未变化。当前上下文保有完整诊断 Skill 和本任务必要 refs，可信目录已确认来源与内容身份均未变化；因此复用当前正文，不重复加载。按交接中的已确认事实、阻塞、证据指针与既定下一只读动作继续；保留原权限边界。若发现后续正文丢失、来源/内容变化或证据失效，只补所缺内容并更新门禁状态。

## B：恢复日志诊断，摘要仅记“此前已加载”，正文已缺失

### 恢复步骤（最多三项优先动作）

1. 以摘要确认最新只读日志诊断目标、权限、已确认事实、未决阻塞和下一动作；保留这些任务状态，不把“此前已加载诊断 Skill”视为当前指令已具备。将所需 Skill 的正文状态记为 `missing`；历史内容身份若未记载，则写“未知”，不可猜测。
2. 从题设已知且可读的原 Skill 路径读取正文，并读取当前任务确实需要的 reference。记录实际来源、本次可核的内容身份、必要 refs 和加载结果；核对本次正文对当前任务的适用性。只补缺项，不全量重读历史、其他 Skill 或无关日志。
3. 当本次所需正文与 refs 已补齐、适用性和权限核对通过后，将正文状态改为 `intact`，门禁改为 `pass`，沿用摘要中的下一只读动作。若新读到的规则与原摘要冲突，保留双方来源并处理冲突；在必要内容仍缺失时保持 `needs-evidence` / `needs-fix`，不靠摘要补造规则。

第一条建议读取命令（仅模板，未执行；需以已知真实路径替换占位符）：

```sh
cat -- '<原诊断 Skill 的已知路径>' '<本任务必需 reference 的已知路径>'
```

若有多个必要 reference，只列出实际需要者。命令读取后还需记录可核版本或 hash；不能因为路径相同就断言内容身份未变化。

### 最小状态记录

```yaml
latest_goal: <原只读日志诊断目标>
phase: <摘要中的阶段>
confirmed_facts: <摘要中仍适用的已确认事实及 provenance/raw pointers>
state_blockers: <摘要中已完成项、未决项和阻塞；保留原值>
scope_permission: <原有只读范围和权限；不扩大>
active_skill:
  source: <已知原 Skill 路径>
  previous_content_identity: <有证据则填；否则“未知”>
  current_content_identity: <待本次读取后填写可核版本/hash>
  required_refs: <当前任务确实需要的 refs 和指针>
  content_state: missing
  after_successful_load: intact
evidence_fallback: <原始证据指针；必要正文/refs 缺失或冲突时停止依赖它们的动作并补证>
next_action: <摘要中既定下一只读动作；待恢复门禁通过后执行>
recovery_check_before_load: needs-evidence
gate_result_before_load: needs-fix
recovery_check_after_verified_load: pass
gate_result_after_verified_load: pass
excluded_context: <过期或无关内容；不把历史“已加载”用作加载证明>
```

上述 `after` 字段是状态转换条件，不是本次已完成的事实。本次没有读取题设中的文件。

### 可粘贴恢复提示

> 恢复摘要中的只读日志诊断，保留其已确认事实、阻塞、权限与下一动作。摘要只记录诊断 Skill 曾加载，当前没有完整正文，不能直接依赖该历史记录继续。先从已知路径补读仍需的 Skill 和本任务必要 reference，记录当前来源、可核内容身份、refs 与 `missing → intact` 状态。核对目标、适用性和权限后再执行摘要中的下一只读动作；只补缺项。必要内容未就绪时保留 `needs-evidence` / `needs-fix`。

## C：名称相同，但可信目录已切换到新来源与新内容身份

### 后续动作（最多三项优先动作）

1. 保留已确认未变化的任务目标与只读权限。依据当前可信目录记录来源路径、内容身份已变化；将旧 Skill 状态标为 `changed`，旧正文只作历史比较材料，移出当前 active instructions。名称相同只可帮助定位，不能作为去重或内容有效性的证明。
2. 从当前可信目录所指的新来源文件读取正文，记录当前来源及可核内容身份，检查它对本任务的适用性和所需 refs。只补读当前必需且缺失、已改变或身份无法确认的 refs。题设仅保证新来源文件可读，没有保证新正文要求的全部 reference 都可读；若缺少必要 reference，明确列出缺项并保持 `needs-evidence` / `needs-fix`。
3. 对照新正文复核受旧规则影响的下一动作、证据要求和已有结论，区分可沿用的独立事实与需要重新核对的流程判断。必要正文与 refs 完整且兼容当前目标/权限后，将新 Skill 记为 `intact`、门禁改为 `pass`，继续原范围内的下一只读动作。任何新增权限要求都不自动获得授权。

第一条建议读取命令（仅模板，未执行；需替换为可信目录提供的真实新路径）：

```sh
cat -- '<当前可信目录指向的新诊断 Skill 路径>'
```

### 仍可复用与需核对的信息

| 信息 | 可以如何使用 | 仍需什么核对 |
|---|---|---|
| 同一任务的目标、诊断对象范围和只读权限 | 直接沿用题设确认未变化的任务约束 | 新正文只能在这些既有边界内适用，不能扩权 |
| Skill 名称 | 保留为检索或展示标签 | 不能由名称相同推断同来源、同内容或已有效加载 |
| 旧来源、旧内容身份及旧正文 | 作为历史 provenance 或必要差异核对依据 | 不能继续当作当前有效指令；旧身份未知时注明未知 |
| 当前可信目录中的新来源及新内容身份 | 用于确定本次应加载哪个文件及预期身份 | 实际加载后记录读取内容身份；核对来源、适用性和所需 refs |
| 交接中若有独立原始证据支持的已确认事实、已完成记录、阻塞和证据指针 | 保留为任务状态与证据索引，不因 Skill 更换而无故丢弃或全量重做 | 核对证据对象、时间和当前相关性；依赖旧规则推导的结论另行复核。题设未列具体事实，本结果不声称这些事实已存在或仍然有效 |
| 旧下一动作、旧流程判断、旧引用集合 | 作为待核对的候选信息 | 是否仍符合新正文、任务阶段及权限；不能直接把旧 refs 当作新正文所需 refs |
| 原始日志、命令输出等动态证据 | 保留已有 raw pointers，必要时按需回读 | 新规则是否改变所需证据及判据；证据是否过期。未给出实际指针时不虚构 |

### 最小状态记录

```yaml
latest_goal: <同一只读诊断目标>
scope_permission: <原只读范围和权限；题设确认未变>
active_skill:
  name: <名称相同，仅作标签>
  source: <当前可信目录的新来源路径>
  content_identity: <当前可信目录的新身份；实际读取后记录可核身份>
  required_refs: <按新正文确定；逐项记录必要性和可用状态>
  content_state: changed
  after_successful_load: intact
historical_skill:
  source: <旧来源；若具体值未给出则待填>
  content_identity: <旧身份；未知则注明>
  body_role: historical_only_excluded_from_active_instructions
reusable_task_state: <目标/权限，以及有独立证据的原任务状态和 raw pointers>
pending_checks: <新正文适用性、必要 refs、受旧规则影响的事实解释及下一动作>
evidence_fallback: <新正文或必要 refs 不完整/冲突未解时，暂停依赖它们的后续步骤并补证>
next_action: <先补读新来源；门禁通过后继续原范围内经复核的只读动作>
recovery_check_before_load: needs-evidence
gate_result_before_load: needs-fix
recovery_check_after_verified_load: pass
gate_result_after_verified_load: pass
```

`changed` 描述当前执行所需的 Skill 与上下文中的旧正文不再一致；并不否认旧正文在上下文中仍完整存在。只有新来源所需正文与 refs 就绪，才能将当前有效 Skill 标为 `intact`。

### 可粘贴恢复提示

> 恢复同一只读诊断，沿用既有目标与权限。当前可信目录中的 Skill 名称虽相同，但来源和内容身份均已变化；上下文中只有旧正文，不能去重沿用。将旧正文留作历史材料并移出 active instructions，先加载新来源正文，核对其适用性、内容身份与当前必需 refs。保留有原始证据支持的任务事实、阻塞和证据指针；复核受旧规则影响的结论与下一动作。必要内容缺失时保留 `needs-evidence` / `needs-fix`，齐备且核对通过后再在原只读权限内继续。

## 交接的共同上下文决策

- `always`：当前目标、权限边界、恢复有效性规则；不把动态日志或临时 refs 固化为长期事实。
- `phase`：本阶段必要事实、状态、阻塞、有效 Skill 身份与正文状态、下一动作。
- `on-demand`：当前仍需且尚未有效加载的 Skill / refs；A 不需重读，B/C 按缺项恢复。
- `raw-pointer`：原始日志、命令结果、争议证据及其可追溯指针；压缩不替代这些原始证据。
- `excluded`：过期或不适用的 Skill、失效目标、失败假设、无关历史；C 的旧正文不得进入当前 active instructions。

本次只生成临时交接验证材料，不写长期 memory 或 AGENTS；无新增 memory 候选，无 archive 动作。未读取或使用可选 schema/attestation 模板，因此不声称执行了 schema 验证。B/C 的恢复门禁尚未在实际诊断环境执行；A 的 `pass` 仅是对题设条件的规则判定。

## 实际读取的 Skill 证据

读取方式：一次 `tools.exec_command` 调用运行 Python；分别对下面两个确切路径调用 `Path.read_bytes()`，在读取后立即记录 UTC 时间，以同一份原始字节计算 SHA256，并输出 UTF-8 正文。未借助目录扫描或读取其他仓库记录。

| 实际路径 | 文内版本 | 本次读取时间（UTC） | 字节数 | SHA256 |
|---|---|---|---:|---|
| `/workspace/scratch/d417066aafa8/agent-dev-kit/skills/adk-context-engineering/SKILL.md` | 2.0.3 | 2026-11-17T12:03:29.326614+00:00 | 3745 | `053f499a34f9a48d3bb1b2b768599ea8951331ef942a03b3e0c50388705313f5` |
| `/workspace/scratch/d417066aafa8/agent-dev-kit/skills/adk-context-compress-handoff/SKILL.md` | 1.0.3 | 2026-11-17T12:03:29.326749+00:00 | 2705 | `caa8bea66bffba468f5033a1a8f841ac14f8c9f7bb4dd922d5a1e911d854649e` |

对应工具结果：`chunk_id=095cea`，`exit_code=0`。这些时间是本次实际读取观测时间，不是文件修改时间，也不是题设中的诊断文件读取时间。
