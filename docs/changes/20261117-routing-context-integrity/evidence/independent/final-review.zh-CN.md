# 独立源码审查：Spec pass / Quality pass

审查者：`independent-reviewer-routing-context-20261117`，独立 AI reviewer。
作者：`ai/root-routing-context-integrity`。本审查者未修改产品源码、Skill、schema、测试、预算或权限字段；只编写独立探针与审查证据。正式时间与逐项摘要绑定见本 change 的 `review-evidence.json`。

## 裁决和精确范围

**Spec：pass。Quality：pass。** 此裁决针对下列完整累计源码差异及已检查的证据包装增量。IR-1、IR-2、IR-3 三项独立发现均已修复并复验，没有尚未解决的 blocker 或 major。此前阶段报告中的 open 状态是当时真实结论，原始记录予以保留；本报告给出最终状态。

| 身份 | 实际值 |
| --- | --- |
| subject / scope | `20261117-routing-context-integrity` / `source-change` |
| 基线 | `6d902f721f560f02883516e809fbd93a326405b6` |
| 审查产品提交 | `713d0d3a85c74bd9fe4b27a23c8dc8b2a066565a` |
| 产品树 | `1f9c586dadb20d6195263cd305efa9e5080291e2` |
| 完整 original.patch SHA-256 | `1b1b1c4d33ed504a36e7796c41421fff7939270a3e8f0b2dc2fbce5f752ace57` |
| 原始观察索引 SHA-256 | `da6836967f0275b8b3e8794ba4df1db238d8daf70c6a22ce130ea14bc181c2fe` |

源码内容在此提交冻结。此后实际包装变更仅涉及本 change 的证据、验证/状态说明以及 `.gitattributes` 中四个精确原始日志/旧 patch 路径的 whitespace 属性。已检查其具体差异；没有针对源码、测试、scanner 或一般路径的格式豁免。记录的 target 保持产品提交，不将后续证据提交冒充已执行完整回归的产品提交。

本记录不签发发布资格，不证明 main CI、不可变 Release、Root 实际接入、native runtime 或设备资格已经完成。验收第 6 项的这些后续阶段仍须按各自实际证据完成。

## 审查方法和证据来源

审查依据为现有操作规则、委托政策、requirements/design、原始测试、原始累计差异以及实际反例。分别读取了缓存/评测实现、路由与权限边界、manifest/schema 兼容变化、四个被修改的 Skill 和新增回归；还检查了 formatter 迁移、删除的私有函数调用点、版本与预注册元数据变化。未采用实施者的通过声明代替独立判断。

独立探针在修复前保留失败，修复后重新运行。数值和读取一致性探针先于最终提交运行，其对应产品实现随后未改变；最终绑定将已复验内容、路由探针记录的源码摘要和最终提交逐一对应。对最终累计差异的 31 个文件检查了 Git 对象与实际文件内容，完整 patch 用 `git diff --full-index --binary --no-ext-diff BASE HEAD` 重新生成并逐字节核对。早期内部绑定曾用不同的 diff header 格式比较，产生的不匹配记录未删除；最终同格式比较为一致，不以该中间记录冒充通过。

65 个 Skill 及 54 个直接参考的全量逐项审查由实施审查记录提供。独立审查核对了 65 个唯一身份与 manifest 的完整对应、54 个唯一直接参考、119 份原始文件的路径/字节数/SHA-256 与基线 Git 对象一致，且每行都有结论和理由；这与声称本审查者重新逐字评审了全部 119 份文件有区别。独立细查集中在实际修改及其调用、权限和回归边界。外部来源取舍保留在 `source-review.md`，不将外部方法介绍当作本产品的执行证明。

最终 102 组完整回归由协调者在洁净 checkout 执行。本审查者独立读取原始输出、时间记录和退出码，并将全部 1082 份运行输入的前后摘要与目标 Git 对象核对；没有宣称自己另跑了一次完整回归。所有复验均为有界无模型观察。

## Spec 判断

| 验收范围 | 独立判断及依据 |
| --- | --- |
| 1. 内容缓存和同次读取一致性 | 原有有界 LRU 保留，phase/relationship 的 schema 也参与内容身份。独立探针在读取后替换同大小、同 mtime 文件，确认摘要来自已解析字节，下一次读取重新检查新内容并拒绝无效输入。原始失败回归和相关测试覆盖内容失效、缺失与编码/校验错误；没有仅依赖 stat 的旧结果旁路。 |
| 2. 禁止 worktree 和同句肯定动作 | IR-2 修复覆盖中英文创建动词及有限限定词/newness/Git 修饰；短触发词不会从否定长动作内复活。独立反例同时包含无关否定与后续肯定控制，没有把整句一律拒绝。 |
| 3. 当前动作、解释对象和权限 | 可选 `requested_action` 类型保持旧 manifest 兼容。ADR 明确动作优先于偶然主题；解释/审查对象与明确实现不同处理。自然驱动实现只扩展既有能力的有界表达。IR-3 的解释误选及修复引出的顺序回归均有原始反例和最终正反复验；未新增或放宽权限字段。 |
| 4. 压缩后的有效内容 | 改后的 context/handoff 文本区分完整正文仍有效、正文被摘要/丢失、来源内容变化，只恢复当前仍需的 Skill/参考。独立最小消费记录演示三种情境，保留失败关闭及当前授权限制；该观察不证明真实 runtime 加载。 |
| 5. 覆盖与现有约束 | 65 项结论覆盖已核对；固定 60 场景与 8 个原 ratchet 均通过，原输入/期望/阈值不变；内核 28930B 仍低于既有 30000B 上限。最终完整回归 102/102。新增负例没有通过改固定期望或放松门禁获得通过。 |
| 6. 版本与分阶段交付 | 源码版本同步为 11.3.15。预注册的 `planned_release` 仅同步版本，未执行的模型计划仍保持未测量状态，任务/holdout/grader/results 未被替换。本 source-change 裁决只完成源码审查阶段，后续 PR/main、Release 和 Root 接入须独立核实。 |
| 7. campaign 类型和有限数值 | 安全字段要求实际布尔值；数值排除 bool，转换失败和非有限/负值拒绝；单条记录与合计都验证。合法零、错误记录和缺失成本语义保留。最终记录的 canonical 一致性检查阻止 Python 等值类型别名绕过。 |

## 独立发现与处置

| ID / 严重度 | 实际问题 | 最终处置 |
| --- | --- | --- |
| IR-1 / major | `10**400` 可产生未归一化的 `OverflowError`；两个合法 `1e308` 耗时相加可产生 infinity，同时被标为完整且通过。 | **fixed**。转换与聚合均经有限非负检查，错误统一为 `ManifestError`。六项原始数值探针修复后重新运行，普通有限值保留，超大整数/溢出按预期拒绝。 |
| IR-2 / major | “不要创建新的 Git worktree”“不创建新工作树”以及英文带 `a git` / `any` 的禁止表达仍可能选中 worktree 写操作。 | **fixed**。有界修饰语语法和包含关系过滤消除短别名复活；原始禁止、相邻肯定及无关否定控制均复验。 |
| IR-3 / major | “请解释编写 ADR 的方法”等被解释动作被当作当前写作；驱动解释请求从基线 abstain/deny 升为实现写操作。初次修复又吞掉“先解释……再执行……”的后续肯定动作。 | **fixed**。局部对象过滤用于触发和任务模式；后续修复仅切开有界先/再顺序，保留为什么/如何/是否等问句对象。原 30 项路由为 30/30；顺序 5 正 7 反为 12/12。旧冻结失效、RED 和基线控制全部保留。 |
| SK-05 / minor | “继续执行已有计划，不要重新拆解任务”在基线已 abstain；既有“按现有计划继续执行”可命中。 | **accepted-risk**。这是既有词法覆盖限制，未被包装为本轮已修复，也不据此声称任意自然语言表达完备。当前验收要求的新增否定/动作与相邻回归已经有界解决。 |

直接证据包括 `campaign-number-probes*.json`、`routing-boundary-probes-expanded-30.json`、`routing-boundary-probes-final-30.json`、`routing-sequential-controls*.json`。阶段报告和较早失败记录用于保留发现过程；最终裁决依据最终内容复验。

## Quality 判断

实际最终完整执行为 2026-11-17 12:26:52.673846–12:32:52.311134 UTC，进程耗时 359.637 秒，退出码 0。`full-timing.json` 含 102 个唯一组且全部 pass；原始 `full-regression.log` 的末尾明确为 `tests=102 pass=102 fail=0`。运行使用同一产品提交的洁净 detached worktree 和位于源码根之外的既有 Python 3.12.14 工具环境。

最终 Ruff、format、strict、release-check 与上述执行均退出 0。独立的 phase 19、relationship 8、最终 materializer 10、runtime comparison 15、routing IR 5 和最终 trigger matrix 32 个测试记录均保留；实施者的 59 个定向测试、固定 60 场景与完整回归有交集，不累加为独立样本总数。formatter 的 AST 与原函数除名称外一致，schema 新字段为可选，原固定路由输入与 profile 阈值逐字节未变。

mypy、ShellCheck、pip-audit 的真实命令、时间、范围和原始日志已核对。mypy 是仓库指定的 20 个文件范围，不是全仓类型覆盖；这些质量观察早于最后路由修复，其被检查的依赖/Shell/指定类型输入随后未改变。最后路由内容另由 fresh Ruff/format/strict、定向测试和完整回归验证。pip-audit 的无已知漏洞输出不构成不存在所有漏洞的保证。

两次不完整执行仍保留为失败/中止：首次旧提交已出现计划版本元数据失败，并因独立发现顺序回归而中止；最终提交第一次源码根执行因工具 `.venv` 被 security fallback 扫描而失败。独立读取原测试和 scanner 后确认后者是测试故意关闭 Git inventory 时纳入根内工具环境；修复验证环境采用洁净源码目录，未修改 scanner、原测试或忽略规则。最终成功记录没有覆盖这些失败历史。

## 最终证据完整性

`audit_final_evidence.py` 在 2026-11-17 12:38:21 UTC 完成只读审计，结果为 `final-evidence-integrity.json`，20 项检查全部通过：

- 封存索引列出的 136 份原始观察全部存在、路径唯一、无 symlink，字节数和摘要逐项匹配；合计 2062950B。
- 1082 份运行相关 tracked 输入在测试前后完全一致；与目标提交所有对应 Git blob 的字节数和摘要一致。覆盖集合排除已明确声明的累计 `docs/changes/`、`reports/`、`evals/results/`。
- 当前工作树相对于这 1082 份输入只有已审查的 `.gitattributes` 包装差异；其他产品输入未漂移。所有包装路径被限制在当前 change 和该属性文件。
- 六个最终执行阶段退出码均为 0；质量原始日志摘要与其记录匹配；两次不完整执行的 130 与未声明通过状态均存在。
- 索引有意冻结原始观察，独立最终报告、审计脚本/结果和 canonical record 是其后新增的独立输出，由 canonical record 另外绑定，不改写原索引。

作者封存观察的完成时间为 12:35:32.676924 UTC。本审查者随后完成上述只读完整性观察。首次写入记录时，本审查者将 finding ID 使用为展示用大写 `IR-1` / `SK-05`，被原 typed validator 的小写 identity 约束拒绝；原记录和实际拒绝保留为 `record-before-typed-id-fix.json`、`record-validation-red.json`。随后仅将机器 ID 规范为 `ir-1` / `sk-05` 等小写形式，未改产品或 validator，语义裁决不变。canonical 的 `evidence_completed_at` 取封存观察、独立核对和记录校验 RED 中最新的实际时间，`reviewed_at` 使用实际形成最终记录的当前时间。

## 保留限制和后续资格

本地负载基线中位数为 73.010ms，最终洁净执行为 87.462ms，高约 19.8%；同一候选较早在另一 checkout 条件下曾为 72.197ms。有限三轮观测未隔离环境影响，不支持确定的加速或回归因果结论。原预算通过；Skill 源字节减少不是 provider Token 或费用下降证据。

SK-05 词法覆盖限制保持；历史 hosted ADC/CMake 超时没有已确认根因，本轮本地成功不证明已根治。上下文三情境消费和合成 campaign 记录均未调用模型/provider。没有运行模型对照、安装 live runtime、操作 SSH/设备/HIL 或取得 native 宿主、Software M5/现场资格。独立 AI 审查不是人类签字，typed validator 只验证记录结构、绑定与允许的范围；语义裁决由本审查者依据上述事实给出。

后续主线/发布/消费者证据可以在保持这些限定下继续工作。若产品源码、测试、权限或预算再次变化，应重新确定目标和相应验证，不能继承此记录对另一组产品内容的通过结论。
