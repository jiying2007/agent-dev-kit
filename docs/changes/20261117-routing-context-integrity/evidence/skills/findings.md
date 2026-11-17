# ADK 11.3.14 全量 Skill 审查与 T3 路由修复

基线：`6d902f721f560f02883516e809fbd93a326405b6`。逐项机器记录为
`skills-audit.json`，包含 **65 个唯一 Skill（56 core + 9 optional）与 54 个直接
reference 文件**的路径、基线字节数、SHA-256、全文审查状态和实质判断。此库存由
`git show <baseline>:<path>` 生成，不把并行实施后的文件冒充基线。

判断统计：58 保留，5 受已复现路由问题影响需修复，2 保留并补上下文恢复方法。
“保留”表示本次有界审查未找到足以支持改动的真实问题，不保证所有行为均无缺陷。

## 已复现与已实施

| ID | 实际反例与影响 | 根因 | T3 处理 |
| --- | --- | --- | --- |
| SK-01 | `不要创建 worktree，在当前分支直接实现该修复` 仍选 `adk-worktree-governance`，并沿实现任务得出 workspace-write；英文禁止创建也误选。 | 长别名已被否定，短别名仍从其内部复活；本地否定语法未覆盖 create/创建。 | 同一否定跨度内短别名继承否定；添加有界创建修饰；跨子句、后续肯定动作仍有效。 |
| SK-02 | `请写ADR，记录接口契约的设计取舍` 被接口主题夺走；`什么是 ADR？` 又误选写作。 | 总短语长度/数量优先于明确写作动作，裸 ADR 被当写作触发。 | 用原 routing.phrase_classes 的可选 requested_action 标明实际作者动作；只对肯定命中排序优先，删除裸 ADR 触发，补更新/写成/记录为等动作。 |
| SK-03 | `请实现 RTOS SPI DMA 驱动，补超时和恢复测试` abstain，实际能力存在却漏选。 | 原触发只识别相邻的“实现驱动”等字面串。 | 复用原动作短语，允许最多 8 个受限 runtime/bus/target 修饰；不以裸名词触发，不跨任意正文/子句。 |

SK-01 证据是 **路由与权限分类结果**，不是系统已实际创建了 worktree 的证据。
Skill 正文本身原已明确尊重禁止创建，本次没有为了增加修改数重写该正文。
SK-02 新字段只影响选主 Skill；任务模式与 mutation permission 仍按既有规则，
只读、否定、域外与按 ADR 实现等反例保留原边界。ADK 对实际模型如何读懂复杂请求
没有在本次取得新证据。

## 方法缺口与保留事项

- **SK-04，上下文恢复方法缺口**：context-engineering / context-compress-handoff
  有目标、授权、状态和 raw pointer，但未明确 active Skill 正文在压缩后被丢弃或
  摘要后的有效性与重载。已交 context 实施者处理；这属于方法完整性观察，未声称
  已复现真实模型丢失正文。
- **SK-05，词法覆盖限制**：`继续执行已有计划，不要重新拆解任务` 在基线 abstain，
  而现有 `按现有计划继续执行` 可选 execution loop。本次 T3 按需求合同收束在
  worktree/ADR/driver 三类；此变体不另扩实施，也不把“全文审查”写成“所有语义完备”。
- token/security/external-intake 三类正文较长，但均含实质权限、原始证据和运行边界。
  没有实际模型 Token/耗时对照，不能仅凭长度认定应删减或宣称降本。
- 既有 RTOS 响应时间假设、ISR/DMA 生命周期、CMake fresh JUnit、IMAP 只读 UID、
  URL 校验连接绑定、source-only/runtime 分层及风险分级方法多数已由前轮修复，
  此轮保留，不重复把已解决事项当发现。

## 证据与验证

- `routing-before.json`：从基线 Git archive 独立提取的源码运行，无模型探针 19 项，
  7 项满足目标；`routing-after.json` 同输入 19 项全部满足。记录完整结果与关键源文件
  摘要，不用只有期望值的表格替代真实返回。
- `routing-tests.log` / `routing-verification.json`：Skill trigger matrix、governance、
  routing IR contract 共 56 个测试通过，含中英文禁止创建、无关否定、后续肯定动作、
  ADR 动作/概念/按 ADR 实现、自然 driver 修饰/否定/只读/域外与可选 schema 兼容。
- `deterministic.json`：原默认 30 项路由场景；`deterministic-60.json`：原固定
  `software_m5_eval_tasks.jsonl` 60 项。输入、期望、grader 均未改变。
- `module-budget.log`：原 30,000 bytes 上限通过；`_matcher_kernel.py` 为 29,107 bytes。
  旧纯格式化函数移入既有 `matcher.py` 的格式化入口，没有新增模块或例外。
- `profile-ratchet.json`：共享工作区当次全部 8 个原 Profile ratchet 通过，未放宽预算。
  ADR Skill 从 3,680 降至 3,663 bytes；这是源码体积，不是实际 Token/费用收益。
- schema sync：检查既有 12 个 packaged mirrors，`pass`、`changed=[]`。
  manifest schema 不在此 packaged registry，只有原 `manifests/manifest.schema.json`
  增加可选字段，未制造新 mirror。

本审查没有调用模型、Codex/Claude runtime、付费服务、真实设备或 HIL。
确定性路由通过不证明 native host 选载或实际任务效果；完整集成、版本/catalog、
独立 Spec/Quality 审查与发布由协调者统一推进。

## 外部原始来源与采用边界

2026-11-17 检索并阅读 Agent Skills 官方资料：

- [Evaluating skills](https://agentskills.io/skill-creation/evaluating-skills)：采用真实请求
  和边界变体、保留既有基线与独立产出检查；实际 token/time 必须实测。
- [Optimizing skill descriptions](https://github.com/agentskills/agentskills/blob/main/docs/skill-creation/optimizing-descriptions.mdx)：
  使用同主题不同动作的 near-miss 负例，不只验证某个固定短语存在。
- [Adding skills support](https://agentskills.io/client-implementation/adding-skills-support)：
  采用渐进式加载与压缩后正文保护/必要重载方法；不据此宣称 ADK 已提供生产上下文管理器。

本次只采用适合当前源码合同的方法，不引入另一套运行时或自动模型评测调用。
