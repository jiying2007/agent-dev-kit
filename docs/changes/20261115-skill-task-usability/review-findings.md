# 11.3.2 候选的独立 Spec / Quality 审查

## 裁决与适用范围

**Spec：PASS；Quality：PASS，范围仅为下列冻结快照的本地 source-change。** 当前没有未关闭的 blocker、major 或 minor。审查发现的性能示例错误传播问题已修复；第一轮验证发现的 profile 体积门槛失败也已修复并在冻结源码上通过完整回归。

这不是远端交付完成或发布批准。11.3.2 仍是本地候选；协调者的完成回执记录远端推送被自动审批拒绝，PR、远端 CI、合并与 Release 尚未发生。必须保留这些未完成状态，不能把本报告替代精确 HEAD 的必需检查或审批。

| 项目 | 绑定值 |
|---|---|
| 审查者 | `ai/root/independent_review`，AI、独立于实现、只读源码审查 |
| 身份保证 | `declared-not-authenticated`；不冒充人类或 GitHub approval |
| Baseline | `c57f4f8a7983f52257c0587eb85881a006e6dc07` |
| 冻结源码 | `092abfed44dabe74d13b2133dd57ac440c8455bb` |
| Git tree | `a4e3b821af71d7bff4ecfdf048dc16417ce3a1e2` |
| 源文件数 | 41 |
| 源码冻结时间 | `2026-11-15T05:18:06.885391Z` |
| 验证证据完成时间 | `2026-11-15T05:27:40.687596Z` |
| 最终审阅时间 | `2026-11-15T05:29:27.176113Z` |
| 原始补丁 SHA-256 | `b098a9087a3d4a1ba1709027ba435909bf83ee1089333d25023a33aab4f4f483` |
| 源快照清单 SHA-256 | `35a9aa968b2ed06fed34f150b25cf961586804458ab2b41ed6739ffe155bda32` |

我没有参与本轮源码实现，没有修改仓库文件、发布、操作用户设备、读取邮箱或运行其他模型任务。仅在 scratch 编写了本报告、独立检查原始结果和摘要绑定。

## 来源与覆盖核验

审查依据为根 `AGENTS.md`、详细 operating rules、本变更的 requirements/design/tasks、实际基线到冻结提交的完整 diff、实现上下文及原始验证记录。41 个路径的工作树字节和对应 Git blob 均逐一匹配 `final-source-snapshot.json`，审阅结束时工作树 clean。保留的 `original.patch` 与实际 Git diff 逐字节一致。

`audit.md` 的表格包含 65 个唯一 Skill 身份，集合与 Manifest 的 56 core、9 optional 完全相等。按注册目录最深归属核算，14 个 Skill 的正文或既有 reference 有修改，51 个保持原资产；嵌套 URL/IMAP 子 Skill 的改动没有误算成父 `adk-data-fetch` 改动。Manifest 除版本号外逐值不变，Agent、Skill、workflow、profile、routing 和路由矩阵身份及权限未扩大。

覆盖记录证明全部职责纳入本轮源审查，不证明每项 Skill 都已被真实模型执行，也不证明全部既存缺陷已经消除。本独立审查完整读取了变更及必要上下文，并核对了保留项的分工覆盖记录；没有把作者的保留结论或 catalog 命中当成真实任务效果。

## Findings 与关闭依据

| ID | 严重性 / 状态 | 触发、影响和实际关闭证据 |
|---|---|---|
| `perf-record-error-masked-by-report` | major / fixed | 中间版本把 `perf record` 与 `perf report` 拆开，采样返回 42 后仍可读取旧结果，并由 report 返回 0 掩盖失败。冻结文档恢复成功依赖链，明确不能消费失败采样的旧结果。独立检查从实际 Markdown 提取命令：record=42 时只调用 record、exit=42；record=0/report=7 时 exit=7；均成功才 exit=0。相邻 callgrind 链也有作者保留的同类负例。这里只证明 Bash 控制流，没有运行真实 profiler。 |
| `profile-source-growth-ratchet-exceeded` | major / fixed | 第一轮全量诊断为 101/102，唯一失败组是 `test_profile_context_footprint`。实现方压缩三个领域 Skill 的重复内容，没有调高任何门槛。最终原 8 个 profile 的 entry/full-source ratchet 全部通过，冻结源码的完整 102 组也通过。初轮诊断没有被包装成最终快照的通过证据。 |

### E1 能力缺口：保留限制，未伪报修复

当前 Manifest 的唯一 low-risk intent 属于只读发现，E1 的低风险实现路径仍不可达。独立实际调用也观察到：README 小修可返回 abstain/deny；一般驱动实现的风险为 unknown，投入为 E2。这里没有可信依据从“小改”关键词授予新的实现权限。

本轮修正了 `micro` 或零匹配可以越过 canonical route 直接执行的文档误导，明确 task-cost 只是预算回执，不能覆盖 `mutation_permission=deny`；operating rules 和 design 也明确 E1 未启用。这个范围决定符合保留权限的非目标。真正 E1 准入仍需要可信风险输入、影响边界和拒绝路径设计，本报告不把它计为已经实现的效率收益。

## 核心行为的独立判断

**Goal 恢复符合只读语义。** 历史 closed/blocked 批次只在 `resume` 放宽选择条件；`plan-check` 与 `render` 继续拒绝不可执行选择。关闭证据引用、依赖一致性、验收映射、状态结构、符号链接及输入边界继续校验。摘要保留阻塞、证据、在途工作、下一动作和历史指针，明确证据内容未验证、运行权限为 false、父 Goal 完成权限为 false。输入中的验证或下一动作没有执行；超出 8 KiB 输出预算明确失败，未静默截断阻塞。未知预算示例使用 null，未设置宿主预算。

**Catalog 只扩大可发现内容。** 它在已经读取的 Skill frontmatter 中检索正向 triggers，保留大小写不敏感、子串匹配、TSV 格式和 core/optional 类型范围。真实公共 CLI 从外部 cwd 查找中英文触发表达均符合预期；optional 命中不被解释成已安装、已加载或有执行权限。

**领域方法的关键差异保留。** API、ABI 与行为兼容分开；旧消费者字节与目标工具决定验证含义，符号表不被当成布局证明。简化示例保留后续清理及副作用顺序。静态分析覆盖头文件消费者 TU，空数据库和管道失败不能冒充零缺陷。GDB 示例先设置目标环境并限制自动加载；制品候选线索与匹配证据分开。RTOS 迭代注明模型前提、IRQ 干扰和上界限制。性能诊断与候选比较分流，并区分 invalid、inconclusive 和 no-gain。测试设计与已授权实施、普通上下文任务与 ADK 资产维护、Pilot smoke 与收益比较均已清晰分开。

压缩后的 offline-core、performance、static-analysis 文件没有通过删除上述关键方法来满足体积门槛。Pilot 的采纳表也改为交独立采纳决策，不因一次通过自动升级默认推荐。

## 已核对的验证证据

以下原始材料位于 `/workspace/scratch/771b38332ec2/candidate-review-evidence/`；独立检查原始文件为同级 scratch 的 `independent-checks.json`。机器摘要绑定见 `independent-review-binding.json`。

| 证据 | 实际结果及边界 |
|---|---|
| 冻结源码完整回归 | `bash tests/run_all.sh --timing-json ...`，exit 0；102 组通过、0 失败，556068 ms，Python 3.12.14。审查者核对了注册组名、原始 PASS 行和 timing 数组逐项同序，102 个名字唯一。此全套由实现流程运行，审查者核验原始结果，没有声称自己另跑了全套。 |
| Goal / planning / convergence | 审查者初轮实际重跑 37 项，通过；同时重跑 `tests/test_catalog.sh`，通过。冻结全套再次包含相应组。 |
| 冻结后的独立检查 | 11 个短检查全部通过，完成于 `2026-11-15T05:23:29.961376Z`。包括混合 closed/blocked 恢复、严格入口拒绝、无关闭证据拒绝、输出超限、真实 catalog 类型/大小写，以及 perf 三条控制流；源码 41 个摘要前后未变。 |
| 领域与 profile | 67 项定向回归通过；8 个原 profile ratchet 全 pass。源体积门槛不等于模型初始上下文、实际 Token 或时延预算。 |
| C 清理语义 | 实际编译并执行 8 种布尔组合。旧早返回示例有 7 个组合丢失后续清理，新例 8/8 保持行为。 |
| GCC / ELF 兼容反例 | 旧消费者搭配旧库通过，替换布局已变但导出同名符号的新库退出 7；新源码重编通过。修订 shell 包装保留 7，构建失败不会误跑旧 executable。 |
| TU / RTOS / GDB 示例 | 头文件变更经真实 GCC 消费者失败；枚举覆盖空格、去重和空数据库。RTOS 仅验证给定公式的数值演算；GDB 仅有 Bash 语法及官方用法核对。它们不构成真实扫描器、板端或 GDB 运行结果。 |
| Strict / format / token | 原始日志分别通过；token-budget 为 65 Skill、零 warning/failure。format 保留已有不可执行脚本模式警告，没有靠批量改文件模式消除警告。 |
| 拷贝及补丁完整性 | 14 份保留材料与对应 scratch 原件逐字节相同；所有来源摘要、补丁和原始日志在绑定 JSON 留存。 |

## 必须保留的限制与交付状态

1. **远端交付未完成。** 完成回执记录 `remote_push=blocked-by-auto-review`、`remote_ci=not-run`、`released=false`。本审查没有尝试绕过拒绝，也不证明公开目的地已取得当前审批。
2. **静态工具有未执行项。** Ruff、mypy、shellcheck 以及真实 clang-tidy/cppcheck/GDB/abidiff 执行未提供；已有 GCC、语法和 TU 枚举证据不能代替这些工具。适用的必需远端/静态门禁仍应在合并和发布前通过。
3. **真实模型和现场效果未测。** 没有模型任务 A/B、原生宿主加载、独立 holdout、Token/费用/时延收益、板端结果或产品资格证据。不能以源码文字、测试条数、文件体积或公式演算声称这些效果已经验证。
4. **E1 仍未接通。** 该项保留为明确能力缺口，不能写成全部自动化路径已优化完成。
5. **作用域为源码候选。** 无安装、用户运行时、设备、模型服务或生产状态变化。后续若修改被绑定的源码，应重新评估受影响验证与审查绑定；公开交付仍走正常审批、受保护 PR 和精确 HEAD 检查。

在上述范围和限制被完整保留的前提下，该冻结源码的需求符合性与质量均可通过；交付状态继续等待远端许可及相应后续门禁。
