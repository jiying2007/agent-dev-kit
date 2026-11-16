# T2 独立定向审查：Review 与随包交接

## 裁决与边界

- Reviewer：`/root/external_skill_scan_v2`，受 `/root` 明确委派；只读审核，没有修改实现。
- 工作树：`/workspace/scratch/2d6ca6dc3d38/adk-practical`。
- 基线/执行时 HEAD：`5b88ec5bce351f68d4756d765e69a4f40bde3f07`。
- 范围：下表五文件相对基线的完整 diff、相关正文与实际导出验证。
- 模式：实施后的独立定向审查；**不是 blind model A/B**。先读实际发布内容和 diff，再读回归断言；随后按授权阅读作者历史 red/green，并独立运行两个相关方法。没有依据预期答案调整 Skill。
- 定向 Spec 一致性：**通过**。
- 定向 Quality：**未发现 blocker 或 major**。
- Blocker：0；Major：0；没有要求修改实现的新增 finding。
- 整体最终 Spec/Quality、完整回归、CMake Skill、预算与发布：仍待 root 统一冻结后审查，本报告不替代那些门禁。

## 快照和实跑

独立运行时间：2026-11-16T00:56:14Z；收尾快照时间：2026-11-16T00:57:47Z。

| 文件 | 审核 SHA-256 | 源字节变化 |
|---|---|---:|
| `skills/adk-code-review-loop/SKILL.md` | `d7bf180c0e288cb4450892f2b6ce0f61625735b43a89745bed0d5a6e76f62cf6` | 7136 → 5888 |
| `skills/adk-code-review-loop/references/review-evidence-template.md` | `14be3cf96eb1d9eed590eb18d216046aca4a09b6a1787a8d82cfc4cb8c4d2c79` | 1987 → 3218 |
| `skills/adk-context-engineering/SKILL.md` | `86dbb451b888eee79923388025f71c1cb92437d3d948ee628b10f24b50807ef5` | 4029 → 3927 |
| `skills/adk-context-compress-handoff/SKILL.md` | `f4d69f46f916f7bc2f5dd734875d3e6fbb5aae94c0ed0d2f95a1d7748b824d7c` | 2615 → 2578 |
| `tests/test_skill_content_contract.py` | `822dcb61d0cbb8c1689247cc0a32f956e33cdc236f2504afff31ad7c6da462c7` | 12250 → 21682 |

四个运行资产合计减少 156 B；测试增加 9432 B。这不是完整 Profile 测量，也不是实际 Token/费用测量。

本审核者实际执行：

```text
python3 -B /workspace/scratch/2d6ca6dc3d38/research-v2/general-review/run-review-tests.py
```

仅加载并运行以下两个已审方法，**2/2 PASS，0 failures，0 errors，0 skips**，约 0.587 秒：

- `test_exported_review_snapshot_captures_selected_target_without_staging`
- `test_exported_context_defaults_are_self_contained`

运行前后及收尾快照的五文件 SHA 一致。另运行所选五文件的 `git diff --check`，退出 0。原始 stdout、回执和实际 scoped diff 均位于本目录；没有通过外部模型或原生 Agent CLI 执行这些验证。

## Review 模板：端点与实际内容一致

当前发布模板先冻结 `review_head`，再根据显式 `review_target` 构造对应参数：

| 目标 | 实际差分 | 文案与证据边界 |
|---|---|---|
| staged | HEAD → index | 使用 `--cached`，不把未暂存修复当成已审；主入口保留 staged `MM` 的 overlay 和 `latest_worktree_reviewed: false` 规则 |
| working-tree | HEAD → 已跟踪 working tree 的净差异 | 明确包含 staged+unstaged 的最终净效果；不包含 untracked 正文，按 scope 单独读取或记录排除 |
| whole-branch | 已核 base 与 HEAD 的 merge-base → HEAD | 不猜默认分支；记录 base、merge-base、head；dirty/untracked 作为独立 overlay，未另审不能声称最新工作树已审 |

这里 whole-branch 的语义已直接写明是 merge-base 到 HEAD，并没有把目标分支自身的新提交混入待审 patch。`git diff --check` 使用相同参数，避免检查对象与正文 patch 不同。

`git --no-optional-locks status` 与 `git -c diff.autoRefreshIndex=false diff` 保留只读取证含义。它们没有暂存、切分支、重置或提交；若基线缺失/无效，模板在输出目标 patch 前失败。文案要求记录实际 diff 身份并在文件变化后重新取证，因此不将一轮旧结果视为持续有效。

### 独立实跑具体覆盖

发布 reference 经真实 `render_asset` 按 claude-code/opencode 两个 target 输出，再从导出内容提取 Bash block；只在 `<project-lint-cmd>` 占位符前运行取证，不执行未指定项目命令。

- 每个 target 实际建立受控 Git 仓，分别覆盖 staged、unstaged、clean committed branch 和同文件 staged/unstaged 混合状态。
- 断言 patch 中出现最终 `TARGET_REGRESSION` 改动，并排除 working-tree 净差分中已被覆盖的 `STAGED_ONLY` 中间状态。不是只检查 exit 0。
- unstaged 场景包含 untracked 文件：status 列出路径，正文不假装包含它；也包含内容相同而 mtime 改变的 stat-only 文件，并显式启用 `diff.autoRefreshIndex=true` 来检验发布命令是否仍保持 index 字节不变。
- whole-branch 在后续 dirty overlay 下仍审已提交 patch，显示 dirty 路径而不混入 overlay 正文；缺失或不存在的 base 必须非零退出且不输出目标 patch。
- 用例验证 index 与目标源文件没有被审查命令修改。

这是两个 target × 四个主要 Git 场景，外加各自的 overlay/无效基线分支；unittest 统计仍记为一个 test method，不扩写成虚假的独立模型任务次数。

### 主入口删简检查

内联 Evidence Template 移除后，唯一完整字段仍在已随包导出的 reference，入口 Commands/Evidence 均明确指向它。independent/author-self-review、机械/语义/readiness 分离、不能将 targeted review 当最终 whole-diff、生命周期 replan、scope、可信 SCM comment 和未审风险判定仍在入口或必需报告字段中。

删去的是重复表达和内联字段副本，未发现授权、独立性或完整审查边界被降低。

## Context/handoff：正文可用与源码辅助分开

两个 Skill 默认使用随包 Evidence Template，不再无条件要求目标仓存在 ADK 源码级 schema/template。只有 ADK 源码根已确认且文件可读时才可选用辅助文件；context-engineering 同时明确未使用就不声称 schema 验证。

当前默认模板都保留：

- 目标、已确认事实与当前状态/阻塞。
- scope/permission，且交接不扩大权限。
- evidence/fallback 与下一动作。
- 各自的上下文选择或 continuity/excluded context 字段。

正文继续区分事实与假设、保留高风险 raw pointer、排除无关完整历史，压缩会破坏权限/阻塞/候选身份可追溯性时停止；handoff 仍不等于完成证据，也不自动写入长期 memory。

### 实际导出与能力界限

独立运行的方法调用真实 `export_assets` 产生 claude-code/opencode 的 core 包，再定位导出的两个 Skill 文件。实际包中不存在源仓辅助 schema/template；导出 Skill 却保留上述默认字段、条件使用语句与权限约束。

这一验证包含真实导出和结构/文本检查，足以核对“默认交接不隐式依赖源码辅助文件”的修复。它**没有让新模型会话执行交接任务**，所以不能据此声称恢复成功率、理解准确率或 Token 费用已测得改善。部分断言检查固定字段/措辞，不能替代本报告对正文语义与原边界的人工式独立审查。

## 作者历史证据与当前权威回执

按授权只读查看了 `/workspace/scratch/2d6ca6dc3d38/audit-general-v2/implementation/` 下的原始记录：

- `red.log`：旧模板漏掉 working-tree/committed 目标，旧交接内容缺少默认自足条件；属于历史负例记录，不是本审核者重新执行的 baseline。
- `red-stat-only.json`：2026-11-16T00:53:29Z，新增 stat-only 场景时两 target 均观察到 index 字节变化，returncode=1。
- `green-final.json`：00:51 的较早快照。该文件名不表示当前最终性，其 template 和 test SHA 与本次审核不一致。
- `green-index-refresh.json`：00:54 的修复后结果，27 个作者执行的方法通过，五个 source SHA 与当前审核一致。

本报告独立实际执行的是前述两个方法。作者的 27 项通过只作为明确归属的历史资料，没有冒充本审核者的执行。root 已说明旧 JSON 原样保留为历史，当前归档依据 `green-index-refresh` 与最新 delivery-final 的 source binding；后者仍应在最终冻结审核时按实际 hash 核对。

## 复核原始文件

- `independent-two-methods.log`：独立 unittest 输出。
- `independent-two-methods.json`：执行时间、结果、运行前后 source SHA。
- `review-snapshot.json`：收尾 SHA、字节变化、diff check 和所读作者记录的摘要身份。
- `scoped.diff`：本次五文件实际差分，SHA-256 `a61276ba3a193c8e06da0e5abdfed8a09b75dbc6778347f720c2d5642439883e`。
- `run-review-tests.py`：独立复跑入口，只加载上述两个方法。

## 同轮额外征询：ADC C11 集成范围

root 在本审查过程中单独请求判断 ADC 的 C11 前置条件。只读检查当前 `adc_scale.c`、header、native test、示例 CMakeLists 和 cross smoke 后确认：`_Static_assert` 在实现内引入 C11，现有两个构建入口未明确声明；公开头和当前测试没有 C11 专属语法。

因此，同意在原 T3 写集明确补齐 `target_compile_features(adc_scale PRIVATE c_std_11)` 与 cross smoke 的 `-std=c11`。PRIVATE 与当前实现范围一致；不必提升 CMake 最低版本或向调用者扩大语言要求。CMake 3.16 官方已列出 `c_std_11`，并明确 PRIVATE feature 作用于目标自身：

- https://cmake.org/cmake/help/v3.16/command/target_compile_features.html
- https://cmake.org/cmake/help/v3.16/prop_gbl/CMAKE_C_KNOWN_FEATURES.html

这是必要的示例集成闭合，不改变 API/验收或引入新门禁。root 已更新计划并要求真实 ADC 项目的 manual-block 用例。**本报告未提前审查尚在修改的 CMake Skill，也未执行本机缺失的 CMake、Ninja 或 ARM 编译器**；新增路径与平台实跑证据留到整体冻结后核验。
