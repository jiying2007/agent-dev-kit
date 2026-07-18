# 负结果记录：harness-team-readiness-v1

## 已验证的负结果

| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-17 | 按 ADK Build 规则从 `knowledge/L2-domain/lessons.md` 检索历史失败 | 对指定路径执行 Harness 关键词检索 | 路径不存在，命令退出 2；转而读取现有 oops-patterns 与 change 负结果 | 不能把不存在的知识文件伪装为已检索证据 |
| 2026-07-17 | 直接吸收文章的 7 维 100 分审计 | 与 ADK product maturity 最短板模型和机械门禁原则对照 | 加权总分可能掩盖 blocked 维度，也缺少可校准样本 | 改用无权重状态与逐维证据 |
| 2026-07-17 | 新建 `harness-audit` Prompt Skill | 检索现有 planning、verification、harness-loop 和 capability 资产 | 方法论已覆盖，新增 Skill 会形成重复入口且难以稳定复现 | 实现 typed deterministic command，复用现有 Skill 和 workflow |
| 2026-07-17 | 直接复制 CodeBuddy/Knot/MCP 配置 | 对照 ADK platform-neutral 与 MCP read-only-first 边界 | 配置与内网平台、凭证和运行时绑定，缺少当前环境授权 | 只吸收可迁移合同，不安装或启用外部系统 |
| 2026-07-17 | 将已经形成结论的 checklist 字段勾选为完成 | 执行 change governance checker | checker 要求保留精确的未勾选合同文本，首次检查退出 1 | 保留机器合同原文，在清单下方另写已形成结论 |
| 2026-07-17 | 首轮定向门禁可直接通过 | 并行执行 format 与 file-mode checker | format 发现旧分析头部 3 处 Markdown 尾随空格；替换旧脚本后 executable bit 丢失 | 用文档空行替代硬换行并恢复脚本权限，再重跑同一门禁 |
| 2026-07-17 | 新 manifest 只声明 source refs 与通用 boundary 即可通过 strict validate | 执行 strict manifest validation | 官方 OpenAI 引用触发专用 `reference_boundary` 门禁，首次退出 1 | 显式补充来源仅作 citation、不得启用 Codex/MCP/runtime/用户目录写入的边界 |
| 2026-07-17 | 所有名为 `example/` 的目录都应视为非实质证据 | 修复审查项后运行正向 readiness fixture | 合法 change-id `docs/changes/example/` 被误排除，正向测试退出 1 | 只排除惯例性的复数 `examples/` 与 template/sample 目录，不按通用 change-id 单词过滤 |
| 2026-07-17 | 根仓 quick gate 应在未提交实现期间全绿 | 执行 56 项 workspace quick gate 并单独复现失败 checker | 54/56；两个失败均源于 strict `agent-dev-kit` dirty，其他 known-dirty 子仓命中既有 baseline | 不自动 commit 或篡改 strict dirty policy；作为 pre-commit 开放项保留 |
| 2026-07-18 | freshness gate 可以接受固定 `--as-of` 以便复现 | 用历史日期执行 `--gate` | 历史时钟可让陈旧 metadata 长期保持 pass | `--as-of` 限定 report-only；gate 强制当天并增加拒绝回归 |
| 2026-07-18 | 任意位置的 OWNERS 都能证明仓库 ownership | 构造 `src/module/OWNERS` 与 freshness check | 嵌套模块 owner 使仓库维度假阳性 | 只接受根与约定 CODEOWNERS 位置，保留嵌套诱骗负例 |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk rg -n -i '<Harness keywords>' agent-dev-kit/knowledge/L2-domain/lessons.md` | 2 | 指定 lessons 文件不存在，负结果已保留并采用受治理 fallback | `docs/changes/harness-team-readiness-v1/negative-results.md` | Knowledge | proposal/design |
| `rtk agent-dev-kit/scripts/devkit.sh propose --change harness-team-readiness-v1 --title '<title>' --owner leiwenjun` | 0 | canonical change artifact 创建成功，初始 stage 为 proposed | `docs/changes/harness-team-readiness-v1/state.yaml` | Workflow | change artifact |
| `rtk rg -n --fixed-strings 'scripts/quality-gates.sh' agent-dev-kit` | 0 | 调用点仅在旧分析/旧 changes 文档，允许保留路径并改为兼容包装层 | `docs/changes/harness-team-readiness-v1/design.md` | Evidence | migration decision |
| `rtk agent-dev-kit/scripts/check-change-governance.sh agent-dev-kit/docs/changes/harness-team-readiness-v1` | 1 | 首次检查发现 Skill Intake 必须保留精确未勾选文本；工件已按合同修正 | `docs/changes/harness-team-readiness-v1/checklist.md` | Workflow | change governance |
| `rtk agent-dev-kit/scripts/check-format.sh` | 1 | 首轮发现 Harness 分析元数据三处 trailing whitespace，已改为段落分隔 | `docs/harness-engineering-analysis.md` | Source | documentation |
| `rtk agent-dev-kit/scripts/check-file-modes.sh agent-dev-kit` | 1 | 首轮发现兼容脚本替换后缺少 executable bit，已恢复 | `scripts/quality-gates.sh` | Source | compatibility wrapper |
| `rtk agent-dev-kit/scripts/devkit.sh validate --strict` | 1 | 首轮发现新 Harness manifest 缺少 OpenAI reference_boundary，已补齐 | `manifests/harness_readiness_contracts.json` | Manifest | source governance |
| `rtk agent-dev-kit/tests/test_harness_readiness.sh` | 1 | 首轮 review 修复把合法 `changes/example/` 当非实质证据；过滤规则已收窄 | `src/agent_dev_kit/readiness.py` | Source Test | HR-003 |
| `rtk agent-dev-kit/tests/run_all.sh --quick --fail-fast` | 0 | quick regression 19/19 通过 | `docs/changes/harness-team-readiness-v1/verification-evidence.md` | Workflow Test | quick gate |
| `rtk agent-dev-kit/tests/run_all.sh --fail-fast` | 0 | full regression 53/53 通过 | `docs/changes/harness-team-readiness-v1/verification-evidence.md` | Workflow Test | full gate |
| `rtk scripts/check-adk-harden-readiness.sh .` | 0 | exact-HEAD baseline 52/52 与 global Codex health 通过；与 working-tree change 证据分层 | `docs/changes/harness-team-readiness-v1/verification-evidence.md` | Workspace Baseline | harden gate |
| `rtk scripts/check-all.sh --quick` | 1 | 54/56；strict agent-dev-kit dirty 导致 current-status/subrepo-state 失败 | `docs/changes/harness-team-readiness-v1/negative-results.md` | Workspace | pre-commit gate |
| `rtk scripts/check-subrepo-state.sh .` | 1 | unexpected_dirty=1，仅 agent-dev-kit 本 change；三个参考仓为有效 known-dirty | `docs/changes/harness-team-readiness-v1/negative-results.md` | Workspace | dirty-state diagnosis |
