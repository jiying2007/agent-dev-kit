# 通用 Skill 实际使用审查：2 个可复现候选

## 范围与证据

- 只读源码基线：`63e8f61ad9a023b4349851ebb4c9a6eca042a119`，候选 v11.3.5。
- 实现仓库：`/workspace/scratch/2d6ca6dc3d38/agent-dev-kit`。
- 反例脚本：`/workspace/scratch/2d6ca6dc3d38/audit-general-v2/reproduce_general_findings.py`。
- 完整结果：同目录 `results.json`，含每条命令、退出码、stdout/stderr、控制组、源码 SHA-256 和实际导出路径。
- 实际产物：`core-exports/claude-code` 和 `core-exports/opencode`。
- 重跑命令：`python /workspace/scratch/2d6ca6dc3d38/audit-general-v2/reproduce_general_findings.py /workspace/scratch/2d6ca6dc3d38/agent-dev-kit`。
- 只在 scratch 创建合成 Git 仓库和导出工件；未修改仓库实现、执行远端写入、运行模型或调用付费 API。

## 候选 1：P2，审查证据命令只覆盖暂存差异，却承载三个审查目标

### 当前路径及触发场景

- `skills/adk-code-review-loop/references/review-evidence-template.md`：`Snapshot commands` 与 `Review Target` 字段。
- `skills/adk-code-review-loop/SKILL.md`：要求先冻结审查对象，目标可为 staged、working-tree、whole-branch。
- `tests/test_skill_content_contract.py::test_exported_review_commands_run_without_optional_wrapper`：当前在空提交仓库上验证命令能运行，尚未验证三个目标真正得到各自补丁。

模板同时接受 `staged | working-tree | whole-branch`，但提供的唯一 patch 输出命令是 `git diff --cached`。`git diff --check` 检查空白错误，无法代替工作树 patch；HEAD 和 status 也无法呈现整分支已提交的改变。

### 实际反例

脚本通过 ADK `render_asset` 读取真正发给消费者的参考文件，提取首个 bash 块中 lint/test 占位符之前的五条 Git 命令，在四个独立临时仓库运行原始命令。每个仓库从 `return cents / 100` 开始；回归内容为 `return cents / 1000`，代码行自带独立 marker。

| 目标 | 模板五条命令退出码 | 模板获得的实际内容 | 直接比较控制组 |
|---|---|---|---|
| staged 阳性控制 | 全部 0 | 含目标回归 patch | `git diff --cached` 同样含回归 patch |
| working-tree，仅未暂存 | 全部 0 | 只有 HEAD 和 ` M fixture.py` | `git diff HEAD` 含回归 patch |
| whole-branch，已提交且工作树干净 | 全部 0 | 只有 HEAD，无变更路径/代码 | `git diff <记录的基线>...HEAD` 含回归 patch |
| working-tree，同文件暂存与未暂存并存 | 全部 0 | `MM fixture.py`，仅 `return cents / 100.0` 的暂存良性修改 | `git diff HEAD` 含真正工作树 `return cents / 1000` 回归 |

此处证明的是模板命令与声明的审查目标不匹配，并非断言真实模型一定漏审。主 Skill 已有 overlay 冻结要求，不能把该已有措施报成缺失；问题在可直接执行的参考示例没有实现目标选择。

### 期望与最小修正

仅调整现有参考模板：先按当前目标选取明确的一组 diff 与对应 whitespace check。staged 使用 `--cached`；working-tree 比较 HEAD 与工作树；whole-branch 先记录真实、已验证的基线引用与 HEAD，再比较 merge-base 至 HEAD。不猜测默认分支名，不把 local overlay 冒充分支审查结果。

当前命令运行性测试可以扩展为上述四个有语义区别的状态：断言输出真实回归代码和正确 baseline，混合状态同时验证没有把旧暂存内容当作最新工作树。不要以 `--cached`/`HEAD` 字符串出现次数作为正确性证明。不需要新 runtime 或新增治理流程。

可顺带一句说明 `git diff HEAD` 不包含 untracked 正文；本轮未将它单独登记为已复现 finding，因为目前四个案例都使用已跟踪文件。若维护者处理这一边界，应保留只读清单和内容读取，不通过 `git add` 改写用户 index。

### 一手资料

- Git 官方 `git-diff`：https://git-scm.com/docs/git-diff 。已打开正文核实 `--cached`、`HEAD` 与 `A...B` 的不同比较端点，非二手教程。
- 本轮并未证明代码审查模型准确率改善；新增验证应只声称目标 patch 选择正确。

## 候选 2：P2，纯 Skill 交接流程依赖没有随包导出的源仓资源

### 当前路径及触发场景

- `skills/adk-context-engineering/SKILL.md` Workflow 5：并行/跨 Agent 时无条件要求使用 `schemas/agent-handoff-v1.schema.json`。
- `skills/adk-context-compress-handoff/SKILL.md` Workflow 3：交接证明可用 `templates/context/continuity-attestation.md`。
- 两个目标资源都位于 ADK 源仓根，而非 Skill 资源目录。
- `src/agent_dev_kit/targets.py::render_asset/render_selection` 与 `compiler.py::export_assets` 只导出选中资产及随附资源。
- README 明确纯 Skill/runtime bundle 不需要 ADK 源码与 Python，因此不能把消费者拥有源仓视作隐含前提。

### 实际反例

首先对所有含这两项能力的 profile 运行真实 renderer：core、release-hardening、personal-core、embedded-fullstack、team-core、large-refactor，共 6 profiles × 2 targets（claude-code/opencode）= 12 组。

12 组均在导出正文保留相应路径，同时导出文件清单中找不到该 schema/template。release-hardening 只有 compress-handoff，其余五个包含两项 Skill。core 每个目标的 render 资产清单均为 57 项。

进一步实际调用 `export_assets(..., ['core'])` 写出两个目标。逐一读取导出的两份 Skill 正文，确认路径仍然存在；在导出项目根和 Skill 根尝试解析该路径，四份正文涉及的八个位置均不存在。完整导出保留在 scratch，可直接验证。

必用 schema 的问题独立成立；可选 continuity template 是同源的较低影响问题，一并修正即可。内联 evidence template 并没有为必用 schema 提供可用文件，也不等于完整机器验证合同。

### 期望与最小修正

优先保持纯 Skill 自足：用现有 Context Policy/Evidence Template 定义最小交接信息（目标、已确认事实、状态/阻塞、scope/permission、证据、下一步），去掉无条件外部路径依赖。若源仓 schema/template 仍有维护价值，明确仅限已确认 ADK 源码根可读时使用；对其他消费者使用内联模板，不宣称经过源仓 schema 验证。

不建议把整份源仓 schema 复制进每个 bundle；当前 large-refactor ratchet 仅余 6 bytes，不能通过放宽预算或添加新 runtime 弥补说明问题。调整应替换/压缩现有重复文字，保留权限不扩张与证据可回读要求。

验证使用真实导出资产，检验无源仓依赖的默认路径确实可执行。若最终改为随包提供依赖，则测试实际文件解析和读取，而非只看文件名出现在正文。

### 一手资料与具体方法

- AgentSkills 官方规范：https://agentskills.io/specification 。正文 `File references` 指明 Skill 引用相对 Skill 根；目录规则将模板/资源放在可随包携带的资产中。
- Anthropic 官方 skill-creator：https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md 。本轮已读取其 `Anatomy of a Skill`/`Progressive Disclosure`：把按需文档与实际模板放入 bundled resources，并给出明确读取条件。当前使用动态 main 页面核查，不冒充固定 commit。这里只借鉴“资源真实随包、按需读取”的方法，未执行其模型评测/安装脚本。
- 前轮已记录的 Sentry 与 Addy 固定 commit URL，本轮 web open 返回 DisabledError；未把失败读取冒充新核查，也不以失败页面支持新增结论。

## Retain：未找到应当改写的独立实证差距

| 已读能力/参考 | 决定与原因 |
|---|---|
| adk-lightweight-planning | retain；已有轻量只读输出与执行衔接，未发现真实反例支持额外仪式。 |
| adk-task-breakdown；task-packaging/vertical-slice-planning | retain；可区分单切片、多切片及 machine dispatch，按真实依赖成图，不强制估时。 |
| adk-planning-execution-loop；long-task-recovery | retain；已有当前状态、最多三项下一步、可控批次及新输入复用。 |
| adk-test-strategy；high-value-tdd | retain；风险分层、独立 oracle/public seam 和非空洞断言已有明确方法。 |
| adk-systematic-debugging；tight-feedback-loop | retain；已有最小反馈、单假设实验和信息增益停顿条件。 |
| adk-test-flakiness-triage；details | retain；重复样本、失败/跳过/缺证与命令退出码边界已覆盖。 |
| adk-prose-revision；review-cases | retain；报告/修订边界清楚，保留事实、单位与引用，不做无证据风格改写。 |
| adk-adr-writer | retain；决策复杂度与读者匹配，选择/事实有据，不强制虚构 alternatives。 |
| adk-token-context-governance | retain；已有按需加载与上下文边界，未另造 token 指标或扩大预算。 |
| review feedback/communication/governance refs | retain 主体；本轮只针对 snapshot 命令实际目标不符，未重复独立性或 overlay 已有要求。 |

## 证据边界

只证明确定性的导出内容、文件存在性与 Git patch 覆盖；没有声称 native host、真实模型行为或平均任务质量被测量。本轮不报告第三项，避免用缺关键词替代 bug。所有实现仍由主代理决定，当前审查没有仓库实现修改。
