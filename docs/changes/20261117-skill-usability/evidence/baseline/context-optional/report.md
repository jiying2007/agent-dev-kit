# Context / Optional Skill 独立只读审查

## 审查结论与边界

- 冻结源码：`78c3be7f6f9b5ee2e557de54156532fb3169198d`（v11.3.13）。审查日期：2026-11-17 UTC。
- 范围：`groups.json` 的 `context_optional` 全部 20 项；完整阅读每个 `SKILL.md`、全部随包 reference，以及存在的 README / OpenAI metadata。逐文件 SHA-256 在 `probe-results.json`，结束前复核没有漂移。
- 已确认两组应处理的问题：归档修复与只读执行合同之间缺少明确交接；两个 optional Skill 的源码工具入口缺少消费者边界，其中组合 Skill 的目录命令还遗漏 optional 清单。
- 一组相关澄清：parallel/planning 的人类任务信封与 canonical v2 JSON 应明确区分。直接转换确实不兼容，但正文没有声称该 Markdown 是可直接提交的 JSON，不能把本轮设计反例说成已发生的派工故障。
- 其余项目保留现状。没有为凑发现数建议新增 Skill、Gate、后台任务、权限层或评测引擎。
- 本报告只证明源码合同、确定性 CLI 和本地夹具结果（现有 E0/E1 范围）。真实模型执行、原生 discovery/load、宿主权限、外部邮箱/网页、生产续行、实际 Token/延迟收益均未测量。

只读仓库纪律：没有修改仓库文件、commit、push、安装原生 runtime 或调用外部服务。导出仅写入本审查目录的隔离夹具。终态仓库只有主代理创建的 `docs/changes/20261117-skill-usability/` 四个未跟踪文档；本审查不拥有这些文件。

## 证据与可重放入口

| 文件 | 内容 |
|---|---|
| `coverage.json` | 20 项的逐项判断、方法/依赖、测试与变更建议 |
| `probe-results.json` | 20 项源码摘要、128 个显式正例、51 个显式反例、128 个自动路由观察、消费者导出与反例 |
| `probe_context_optional.py` | 公开 matcher、实际导出及 optional 安装选择的可重放探针 |
| `contract-edge-results.json` | catalog 缺口、Markdown 信封直接转 v2 的拒绝结果与合法映射对照 |
| `probe_contract_edges.py` | catalog / v2 边界探针；不改变 validator |
| `catalog-skill.tsv` / `catalog-optional-skill.tsv` / `catalog-all.tsv` | 同一可信 Manifest 的公开 catalog 原始投影 |
| `tests-contracts.log` | 74 项实际通过；另保留首次 Goal convergence 的测试入口导入错误 |
| `tests-goal-convergence.log` | 修正测试调用的 PYTHONPATH 后，9 项通过 |
| `tests-methods.log` | IMAP 本地协议、序列化、readiness、secret scan、flaky sample 共 33 项通过 |
| `tests-export-context.log` | 上下文/并行包消费者自包含、父 fetch 状态、未知 archive hash 共 4 项通过 |
| `negative-results.md` | 已排除假设、测试调用错误及证据限制 |

本轮实际通过 120 项已有定向测试。初次 `tests.test_goal_convergence` 导入失败是调用方式缺少 `tests` 路径，不能记为源码缺陷；保留首次日志，仅重跑这 9 项，未重跑其他已经成功的模块。128 个显式 trigger 均匹配各自 Skill，51 个显式 non-trigger 均拒绝；这只能说明词面合同，不能证明自然语言任务质量。

两个导出目标 `claude-code`、`opencode` 均成功导出 20 项。父 `adk-data-fetch` 单独选择时只含父正文；选择 URL 子 Skill 时只含 URL 子项；父 + URL 不携带 IMAP。嵌套源码目录没有隐式扩大安装范围。

重放环境：CPython 3.12.14；从冻结 ADK 源根使用本工作区已校验的 `rtk`，并设置 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src`。`probe_context_optional.py` 拒绝覆盖已有导出目录；如需再次重放，应给探针单独的新输出目录或保留旧证据后另建副本，不删除旧证据。

## F-CO-01：归档修复步骤与只读执行合同没有闭合的实施交接

**优先级：P2。证据：source-contract + 本地公开 matcher 重放；不是原生宿主故障。**

### 当前证据

- `skills/adk-archive-governance/SKILL.md:3` 声明“检查和修复现有归档”；`:31–32` 的 Goal 也包括修复 meta/topic/hash。
- `:39–46` 的 Workflow 直接从检查进入最小修复、查询验证与项目总检查；`:43` 要求补 meta/topic、规范文件名、标记 superseded，并已正确要求未知 hash 差异保留原证据。
- `manifests/skill_content_contracts_v2.json` 中 `adk-archive-governance` 仅覆盖 `capability_class=guardrail`、`runtime_role=primary`、`selection_group=archive-governance`；其 `governance` category 继承 `effect_ceiling=read-only`。
- `src/agent_dev_kit/matcher.py:263–269` 明确将只读 ceiling 的 `mutation_permission` 约束为 `deny`。这是权限上界，不是错误的授权检查，不能因为用户文本写了“已授权”就绕过。

### 反例与对照

公开 `match_text` 输入：

> 请修复归档元数据，已明确授权修改 docs/archive 的 topic 和 meta，不删除历史文件。

结果为 `skill=adk-archive-governance`、`task_mode=implementation`、`effect_ceiling=read-only`、`mutation_permission=deny`。该 Skill 没有把实际修复交给已经获准的 implementation owner，正文却继续要求执行修复。读者只能自行补出“谁写、如何交回验证”的流程。

对照“请检查已有归档元数据，先给只读报告。”正确返回 `readonly/deny`。未知 hash 的只读输入同样未获得写权限。原始输入/完整返回见 `probe-results.json -> cases.archive-*`。

### 影响和测试缺口

这是**方法与执行责任不一致**：遵守 matcher 的执行者可能重复请求授权或停在报告，直接照 Skill 操作的执行者则可能越过自身只读角色。没有真实宿主 trace，因此不声称这些行为已经发生。

现有 `test_archive_unknown_hash_mismatch_keeps_original_evidence` 验证了 hash 证据保留，trigger 测试验证了能找到 Skill；均未检验只读治理角色与修复实施角色之间的交接。

### 最小修复

保持现有 effect ceiling、validator 和权限判定。明确治理阶段只输出证据、最小候选 patch/修复 task；当现有会话/任务已有实施授权时，把该 task 交给**既有** implementation owner/primary，实施后回到该 Skill 做 archive 查询与验证。既有授权不重复索取；无授权或没有可用实施 owner 时，保留候选并给出具体 blocker。不要新增 Skill，不让自然语言授权自行升权。

### 验收

- 正例：已有受信 implementation 合同的归档修复，产生具体最小修复 task，沿用现有 owner 和授权，修复后核 topic/meta/hash/查询；不再次要求同一授权。
- 反例：纯只读检查只输出 findings；未知 hash 不能通过“交接”变成自动重算；不删除历史材料；没有实施 authority 时不能自行写入。
- 确定性检查仍需保持上述 matcher 两种请求的 `deny` 上界；另用任务包/候选产物检查证明实施交接字段可执行，不以新增一句口号为通过标准。

## F-CO-02：optional 消费者命令依赖未限定源码根，初始目录查询漏掉 optional

**优先级：P2。证据：实际导出 + 命令失败重放 + canonical catalog 对照。可作为同一个窄范围方法修复。**

### 当前证据

- `optional-skills/adk-skill-composition-governance/SKILL.md:35–37` 明确涉及 skill、optional skill、目标 profile。
- `:40` 的轻量路径要求现有 matcher/negative/collision case；`:75–83` 列出 `bash scripts/devkit.sh catalog ...`、`match`、strict validation 和 tests，没有注明这些只存在于核实后的 ADK 源根，也没有消费者缺失时的 source-check 状态。
- `optional-skills/adk-security-supply-chain/SKILL.md:70–85` 的工具示例中，`:76` 同样直接列 `bash scripts/devkit.sh validate --strict`。它与候选资产路径扫描混在同一段；正文没有给该 ADK 专用命令限定 cwd。
- `src/agent_dev_kit/targets.py:289–337` 只渲染 Skill 正文及目标声明的 support directories。两个真实导出都不含 `scripts/devkit.sh`、源码 `manifest.json` 或根级 schemas/templates。这是合理分发边界，不应通过把整套源码打进 Skill 解决。

### 可执行反例一：消费者没有源码 helper

从实际导出的两个根分别执行组合 Skill 的首条公开命令：

```bash
bash scripts/devkit.sh catalog find --keyword adk --type skill
```

均返回 `127`：`scripts/devkit.sh: No such file or directory`。同一命令在已核 ADK 源根返回 0，排除命令语法本身错误。目录、argv、stdout/stderr 和返回码见 `probe-results.json -> exports`。

security 的 `validate --strict` 引用相同缺失文件；本轮没有对消费者重复执行它，也没有运行漏洞扫描器或未知候选脚本。文件缺失足以确认该发布命令在此包内不可用，不把未运行的 security validation 写成已复现通过/失败。

### 可执行反例二：源码根的目录查询只返回 56 core

组合 Skill `:77` 的 `--type skill` 精确映射 `manifest.skills`。公开 `catalog_contract.find_rows` / CLI 得到 56 项，没有任何 optional。现有 `--type optional-skill` 对照返回 9 项，包含 `adk-email-imap-fetch`、`adk-fetch-url-content` 两个嵌套来源及组合 Skill 自身。两查询合集精确等于 Manifest 的 65 个 Skill。

对应代码是 `src/agent_dev_kit/catalog_contract.py:154–179`，尤其 `:160–163` 的类型分支。原始表在 `catalog-*.tsv`，集合差在 `contract-edge-results.json -> catalog`。

**限制**：`:79` 的递归 `rg --glob SKILL.md` 已覆盖嵌套目录，后续步骤可能补回触发信息。因此本报告只认定初始 namespace/description 盘点不完整，不声称所有实际审查一定漏掉 optional。

### 影响和测试缺口

消费者要么得到不存在命令，要么自行寻找来源、错误地在目标项目运行 ADK 验证。源仓组合审查若仅依据第一条描述目录，会在比较候选时漏掉 optional 能力和排除边界。

已有 export self-containment 测试覆盖 context、parallel 和其他部分帮助文件；`test_published_trigger_scan_covers_the_manifest_including_nested_skills` 只验证后面的 rg，不验证前面的 catalog 命令。security 测试覆盖扫描样例的脱敏与退出码，未覆盖 ADK 源根依赖。

### 最小修复

1. 两个 Skill 均给 ADK 源码专用命令添加清楚的适用条件：只在已核源码根及 helper 可读时运行；消费者优先使用项目已有可信入口，缺失时将相关源码检验标为 `not-run/unavailable`，输出可审查候选及确切限制，不安装未审依赖、不伪报 validation。
2. 组合目录查询覆盖现有 `skill` 与 `optional-skill` 两类；可以复用现有两条 bounded catalog 查询，不另建 registry。不把目录可见当安装回执。
3. 保持 optional 显式选择、权限和 fallback 边界。该修复不扩大安装或执行权限。

### 验收

- 正例：可信源码根中，两查询的 Skill ID/路径合集等于 Manifest，包括嵌套 optional，无 Agent/Workflow 混入；缺少某类结果不能当完整盘点。
- 正例：真实导出保留 references，正文不再把缺失 helper 当默认消费者命令；不需 ADK Python/源码也能完成边界明确的报告。
- 反例：纯 Skill 包没有源码 helper 时不从网络安装、不执行候选脚本、不声称 matcher/strict validation 已通过；被排除或未安装 optional 不能因 catalog 命中而加载。
- 保留父 fetch 只选择父、父+URL 不携带 IMAP 的现有正反输出。

## C-CO-03：人类 Worker 信封与 canonical v2 的映射应明确

**状态：非阻塞澄清；与已有 task-breakdown 修复联动。证据：source-contract + 独立 validator 反例；不认定已发生运行缺陷。**

### 当前证据和反例

- `skills/adk-parallel-agent-governance/SKILL.md:37、41、50` 提到 v2 合同/permission/exit，并默认使用随包 `references/parallel-worktree-task-package.md`。
- 该 reference `:5–32` 实际是 `md` fence 的 `[parallel-task]` 人类派工信封；有 25 个字段，包括 scope、global_constraints、interfaces、ready_to_handoff、report/noise policy。它**没有**声明 `structured_output_schema`。
- `skills/adk-planning-execution-loop/references/long-task-recovery.md:69` 是“Task Package v2”方法速记，紧接 scope_read/scope_write/must_not_touch，但未给序列化映射。
- `src/agent_dev_kit/intent_boundary.py:13–34、81–100` 严格限定 canonical 顶层字段；scope 等不是合法顶层键。

独立填充 reference 的字段后直接提交 validator，得到 11 个缺失 canonical 字段和 18 个额外字段；在一个已通过的 v2 payload 上单独加 scope_read/scope_write/global_constraints/interfaces/ready_to_handoff，分别得到 `unexpected fields`。该负例只证明“不能直接转换”，不证明人类模板本来就承诺能直接转换。

对照不改 validator：把 scope、global constraints 和接口约束保留为 `constraints` 字符串数组；owner/task ID/证据/报告入口放 `context` 或宿主外层信封；交接完成条件进 `done_when`，状态放报告；其余使用现有 canonical 字段。实际返回零错误。完整 payload/返回见 `contract-edge-results.json -> task_package`。

### 最小澄清与验收

- 若本轮正在修复 task-breakdown 的确证字段不兼容，连带在这两处加“人类调度信封不是 v2 JSON；宿主要求 v2 时如何映射”的短说明，避免同概念三种说法。
- 保留读写 scope、禁止路径、共享接口、owner、report/noise、ready 条件；不删除安全信息，不放宽 strict validator，也不创建第二份 schema。
- 正例：抽取随包示例或现有映射后得到可由真实 `validate_task_package` 接受的 research/implementation payload；scope 信息可在 `constraints/context` 或明确外层信封找回。
- 反例：直接把外层字段塞到 v2 顶层仍拒绝；research/prototype/decision 不能获得 approved implementation 权限；不把人类信封检查标成实际派工成功。

## 20 项覆盖与保留判断

“无新 finding”表示本轮没有足够证据建议修改，不等于模型效果或生产质量认证。所有项目都做了全文、随包引用、显式触发/排除、Manifest/v2 元数据和两个消费者导出检查。

| # | Skill | 显式正/反例 | 方法与依赖判断 | 结论 |
|---|---|---:|---|---|
| 1 | adk-runtime-router | 8 / 3 | 唯一 primary、fit/abstain、optional installed inventory、已有计划续行均有明确分支；源码命令已限定；reference 按冲突加载 | 保留 |
| 2 | adk-context-engineering | 6 / 3 | stable/task/evidence/on-demand 分层；模板可独立导出，根 schema 可选；6 个自动触发按现行合同提升给 token primary | 保留；记录角色观察，不擅改既定路由 |
| 3 | adk-token-context-governance | 17 / 3 | L0–L3 与 raw fallback 清楚；普通压缩不依赖内部 Python；真实用量缺失不能报收益 | 保留 |
| 4 | adk-parallel-agent-governance | 7 / 2 | scope 隔离、共享 owner、data-only、只读 reviewer、whole-diff 收口完整；随包包可用 | C-CO-03 只澄清信封映射 |
| 5 | adk-worktree-governance | 6 / 3 | stay-current、dirty 保护、真实隔离价值、授权/清理和资源独占清楚；无多余心跳 | 保留 |
| 6 | adk-context-compress-handoff | 7 / 3 | 目标/失效目标、raw refs、权限、最多三动作、excluded context；导出模板自包含 | 保留 |
| 7 | adk-goal-authoring | 5 / 4 | 原验收分母、边界、current-state、批次与只读 resume；未知预算不造数；24 个 Goal authoring 真实解析/CLI测试在本轮通过 | 保留 |
| 8 | adk-planning-execution-loop | 5 / 4 | 已批准计划按差异续行、未知外部 effects 对账、无进展退出、批次/父目标区分；9 个 convergence 测试通过 | C-CO-03 仅修 recovery 的 v2 速记精度 |
| 9 | adk-memory-curator | 7 / 2 | report-only、证据/冲突/脱敏、人工晋升与回滚；无外部 memory 写入器假设 | 保留 |
| 10 | adk-archive-governance | 8 / 2 | 原 hash 差异保护正确，但修复步骤缺少从只读治理到既有实施 owner 的交接 | F-CO-01 |
| 11 | adk-knowledge-archive | 8 / 2 | 新候选与治理修复分开；路径不明 blocked，保留数字/否定/证据，不自动晋升 | 保留 |
| 12 | adk-external-practice-absorption | 8 / 4 | source-only/scoped-adoption/portfolio/eval 分支；LLM_AGENT/ADK 源根限定；owner/curator 分离、未测不报效 | 保留 |
| 13 | adk-data-fetch | 3 / 2 | 三独立 optional、子项缺失停止、partial/not-verified 向上传递；父/子独立导出对照通过 | 保留 |
| 14 | adk-email-imap-fetch | 3 / 1 | 有界 EXAMINE/UIDVALIDITY/BODY.PEEK；日期、精确地址、缺失项与 MIME 分支；15 个本地方法测试通过 | 保留；真实邮箱未测 |
| 15 | adk-fetch-url-content | 3 / 1 | 公开 URL、DNS绑定与每跳拒绝、robots/预算/内容/相对链接/partial 分支；无实际抓取实现随包 | 保留；真实网络工具适配未测 |
| 16 | adk-test-flakiness-triage | 3 / 1 | 真失败和环境噪音分开，单变量、有界采样、独立同分布统计前提、quarantine不算PASS；样例退出/取消/证据保留通过 | 保留 |
| 17 | adk-security-supply-chain | 5 / 2 | 范围分层、source-to-sink与覆盖区分、synthetic序列化反例、脱敏命令测试通过；源仓validator缺cwd限定 | F-CO-02 |
| 18 | adk-prose-revision | 8 / 6 | report/revise分开，用户已请求改写不加批准轮次；保数字/术语/否定/引文；不伪装AI鉴定 | 保留 |
| 19 | adk-incident-rca-report | 4 / 1 | 稳定后RCA、时基/采集区分、unresolved、可选5-Why、未知owner；现行合同为显式fallback | 保留 |
| 20 | adk-skill-composition-governance | 7 / 2 | collision-only避免全量流程，源合同与行为证据区分；命令源码边界/optional namespace盘点不足 | F-CO-02 |

## 不应由本轮证据推出的结论

1. `adk-context-engineering` 的六个自动 trigger 提升到 token primary 是现行 `selection-group:context-policy` 的有意合同，已有测试明确要求该行为。它在 `--skill` 显式路径仍可独立命中。自动返回没有保留 supporting 入口值得后续真实 trace 观察，但不能仅凭本轮看到“名字不同”就更改 primary。
2. fetch 三项与 incident RCA 的自动匹配因 `explicit-only` 而 abstain，显式 `--skill` 仍可用；目录命中不等于安装。不能为了更高命中率删除这些边界。
3. 所有本地模拟 IMAP/条件变量/序列化/采样结果都属于测试自有程序；ADK Skill 没有因此变成生产 IMAP 执行器或获得真实工具权限。
4. 没有测量过模型任务完成率、Token、恢复轮次、用户打扰或降噪收益，均应保留 `not-measured`。
5. 本轮未引入需要查新的外部 API 事实；判断依据为冻结仓库、公开本地接口和已执行输出。没有把随包 RFC/上游链接的存在写成已重新完成官方事实核验。

## 建议实施顺序

先完成 F-CO-01 的角色交接精度和 F-CO-02 的消费者/目录完整性。若 task-breakdown 本轮确证的 v2 映射修复合入，再同步 C-CO-03 两处措辞及一个实际 validator 的映射对照。维持现在的 strict contracts、explicit-only optional 和所有拒绝路径；其他 15 项不因本轮审查而改写。
