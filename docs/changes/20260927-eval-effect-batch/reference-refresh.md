# `llm_agent` 参考仓远端复核与 ADK 吸收筛选

复核时间：2026-09-27。来源：`llm_agent/manifests/reference_pins.json` 的 exact pin、各仓 `git ls-remote`、GitHub compare、上游 README/Release Notes。只读元数据与可见文档；未更新本地参考 checkout、运行上游代码、改 registry/pin 或启用 runtime。多个参考目录有既有 dirty，禁止用 `pull/reset` 代替审查。

## 已登记来源的变化

| 来源 | pin → 远端分支 HEAD | 相对 pin | 本轮判断 |
|---|---|---:|---|
| [OpenSpec](https://github.com/Fission-AI/OpenSpec/releases) | `3c7a05c5dc88b2397c478805890b55ed392b19e8` → `79b6aa9c98f1e36795b2bc4ef2a8f770c6d3a777` | +347 commits | 继续优先审查；v1.12 的 findings report 和 v1.13 的验证范围披露可作方法参考，不导入 CLI |
| [superpowers](https://github.com/obra/superpowers/releases) | `6efe32c9e2dd002d0c394e861e0529675d1ab32e` → `8ca22dba9a94f28898bbce59f2537ff4d87c747d` | +245 commits | v6.4 的连续执行、里程碑末整体审查可适配现有规划 Skill；不启用其插件或自动更新 |
| [mattpocock/skills](https://github.com/mattpocock/skills) | `ed37663cc5fbef691ddfecd080dff42f7e7e350d` → `c55ee46073ed923f86ce59a5eb3b6d895095d1b7` | +158 commits | spec 执行 Skill 仍在 upstream `in-progress` 目录；依赖图与 ADK task-breakdown 大部重合，只补就绪集合重算与阻塞证据，不导入该 Skill |
| [planning-with-files](https://github.com/OthmanAdi/planning-with-files) | `d71b3be47b62fe49d60fb2ede800e1907ebea3d9` → `51c1caa27f9fefe259e45a7cc92fa79ee8787cd7` | +222 commits | 新增跨工具计划/attestation 脚本；ADK 已有状态、恢复、continuity 规则，hooks/注入脚本不进入 runtime |
| [oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex) | `f947e3a41c062c25fd107686862b68ee5d1b66a5` → `cdc24a71408ebd6bd0362f52170f0d7998f77007` | +817 commits | 变化面很大且是独立 Codex runtime；只读方法观察，禁止作为 ADK/Codex fallback |
| [digital-worker](https://github.com/jiying2007/digital-worker) | `4a94231d26df1aeaeba336e6a4e2327db5a3bd44` → `6160b33862a3b077fe8d2a21ab1a15416491cf0b` | +121 commits | 独立 Software M5 试点身份，须另行审查真实功能/现场证据，不能作为外部实践自动吸收 |
| [vibeflow](https://github.com/ttttstc/vibeflow) | `0df764eff5e7b034611540da8d9f8367dfae55b2` → 同 SHA | 0 | 本轮无需重复吸收；本地目录有既有 dirty |
| [scale-engine](https://gitee.com/hongmaple/scale-engine) | `ace49169c4191db656989b738f31edb19a380a63` → 同 SHA | 0 | 本轮无需重复吸收 |

提交差额来自上游 compare，表示 pin 到远端分支 HEAD 的提交数量；不等于本地可安全快进，也不等于全部变更值得采纳。OpenSpec、superpowers、vibeflow 的本地参考 checkout 已有大量脏改，均未触碰。

## 新候选与更优来源

| 候选 | 上游状态与适用范围 | 决定 |
|---|---|---|
| [OpenAI Plugins](https://github.com/openai/plugins) | HEAD `1dc195897af4161d039b80d8471ec0a10c9bbc89`；OpenAI 官方现行 Codex plugin 示例；[旧 `openai/skills`](https://github.com/openai/skills) README 已声明弃用。适合 `~/codex` 分发包装对照，非 ADK core 运行时 | `adapt/observe`：后续按 exact commit 核插件 manifest 和许可；不直接注册或安装 |
| [GitHub Agentic Workflows](https://github.github.com/gh-aw/introduction/architecture/) | HEAD `60ff367876c6c71755b36c5e91e103dcab1fe223`；GitHub 官方、MIT；安全架构把隔离、声明式权限、待审写入分层。其 README 也列出已退役的受漏洞影响版本范围 | `adapt`：只对照 ADK 工具副作用契约和验证范围；不安装执行器，任何试用须先审 exact 版本与安全公告 |
| [Anthropic Skills](https://github.com/anthropics/skills) | HEAD `33375500bcea98d610eb30ce10ac4e59b89c390d`；官方 Skill 样例仓，单项许可及执行资产差异需逐项审查 | `observe`：仅在 ADK 现有 Skill 出现明确缺口时抽样，不批量复制 |
| [superpowers-skills](https://github.com/obra/superpowers-skills) | HEAD `cdcd624ad3fd8026deb692e565351854569798dd`；上游仓已于 2025-10-27 归档；旧 release notes 的拆仓方案不是现行维护事实 | `reject`：继续以活跃的 `obra/superpowers` 现行仓为来源 |

## 本地吸收决策

1. `adapt`：把同一逻辑目标的连续实施、定向检查和里程碑末整体验证写入既有 `adk-planning-execution-loop`，减少每个小点都跑全仓体检和 PR 的开销。出现共享契约、权限或发布边界变化时仍即时执行对应门禁。
   - 当前 ADK profile 解析没有默认选中该 Skill，资产分类将其标为按需使用；这项源码优化不代表任何默认 Runtime Bundle 或 Codex live 已更新，后续分发须按独立来源锁验收。
2. `adapt`：`gh-aw` 的待审写入模型补强既有 `adk-interface-contract-design` 参考契约，区分 proposal、可信校验、受限 executor、执行回执和目标生效；不引入 GitHub Actions 执行器。
3. `adapt`：mattpocock/skills 的 task graph 就绪前沿，只补 `adk-task-breakdown` 的前置验收、共享写冲突与重新计算规则；沿用已有 task-package v2，不复制其 tracker 或并行运行时。
4. `archive-only`：OpenSpec 的 findings report 与验证范围披露已对照现有 Evidence Index 和 Completion Guard；本轮没有证据要求新增一套 CLI 或 schema。
5. `reject`：不批量升级 pin、不自动 clone/执行第三方仓、不把活跃参考变成 ADK runtime fallback。新仓若要进入 `llm_agent` registry，另走 candidate、独立 owner decision 和安全审查。

以上是本地 research/review 结论，尚未形成根仓 adoption decision 或 Knowledge Hub active 事实。

## 2026-09-28 再核与补充候选

根仓隔离 worktree 的只读远端审计再次检查全部 8 个已批准 pin：6 个 `different`、2 个 `same`、0 个 `unavailable`，与上表 SHA 一致。审计输出绑定 pin manifest SHA256 `0b12798f00db011d0a5a3fa919ee667ac960b8294435653bfd8af651947bca1c` 和 registry SHA256 `9ebb5e25882ccaea7d4852954924883e1bf0c8588154dbf23fa5ec3331d3cc6f`；未检查祖先关系，不能据此自动更新 pin。
2026-09-28 06:18:56 UTC 再次只读观察全部 8 仓，仍为同一组 6 different/2 same exact SHA；观察时间不是 pin 提升、提交祖先关系或方法内容复审证据。

| 新线索 | 直接读取与适用范围 | 决定 |
|---|---|---|
| [OpenAI Plugin Eval](https://github.com/openai/plugins/blob/main/plugins/plugin-eval/README.md) | 官方 `openai/plugins` 内的本地 CLI/插件示例；其 [package.json](https://github.com/openai/plugins/blob/main/plugins/plugin-eval/package.json) 声明 Node.js ≥20、私有包和测试入口。适合对照静态分析、运行时 benchmark 与报告分层 | `observe`：ADK 已有 Python 3.8 eval/footprint 入口；不引入 Node、插件 runtime 或打分器。若后续导入单项资产，先锁 exact commit、许可与测试身份 |
| [Langfuse](https://github.com/langfuse/langfuse) | 活跃开源的 trace/dataset/experiment 平台；其 [数据集文档](https://github.com/langfuse/langfuse-docs/blob/main/content/docs/evaluation/experiments/datasets.mdx) 支持按版本时间重跑，核心 OSS 声称 MIT，但 Enterprise 目录另有许可；自托管默认有基础遥测 | `archive-only`：版本化数据集和实验可作 ADK 证据设计对照；平台服务、遥测和外部存储与本批 Python 3.8 本地边界不合，暂不列为运行依赖或新增 pin |

本批新吸收点是结果语义校准：确定性路由评测即使输入含 `expected_safe`，也只能报告路由匹配；安全判断显式 `not-evaluated`。来源为 [OpenAI Agents SDK Testing](https://openai.github.io/openai-agents-python/testing/) 的测试边界和 [OpenSpec v1.13.2](https://github.com/Fission-AI/OpenSpec/releases/tag/v1.13.2) 的验证范围修复。未复制外部实现。

根仓 `check-reference-source-integrity.sh` 使用专用 Python 3.11 环境复核通过；系统 Python 3.8 会在根仓工具的 `Path.is_relative_to` 处失败。该环境差异不影响 ADK 自身 Python 3.8 合同，也不能把参考仓的远端更新解释为本地 pin 已提升。
