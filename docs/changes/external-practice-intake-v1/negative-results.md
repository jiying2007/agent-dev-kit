# 负结果记录：external-practice-intake-v1

## 已验证的负结果

| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-19 | ADK lessons 已有可复用 intake 结论 | 检索 `knowledge/L2-domain/lessons.md` | 文件不存在 | 保留负结果，不伪造历史经验；以当前 proposal/design 为新基线 |
| 2026-07-19 | 旧 OSS schema 可直接扩展到官方文档与微信 | 对比 `oss_discovery_sources.json`、candidate keys 与微信/official records | repository score/stars/forks/archived 字段无法表达文档 authority、版权、body boundary | 不叠加 nullable 字段，硬切统一 practice schema |
| 2026-07-19 | 每个来源独立 Agent/Skill 最清晰 | 检索现有 Skill/Workflow/官方与微信入口 | 会复制安全、freshness、decision、release 逻辑并扩大路由冲突 | provider 只做 adapter；单一 curator + Skill + Workflow |
| 2026-07-19 | Gitee 搜索空列表可以视为“没有候选” | 核验 Gitee API 文档及 2025–2026 官方 feedback issue | 官方 endpoint 存在，但有公开空结果异常报告 | 空结果必须 `degraded-empty`，不能作为 clean pass |
| 2026-07-19 | 保留旧命令 warning wrapper 可降低迁移风险 | 对照用户“硬切换、不兼容、去残留”与当前双入口风险 | wrapper 会延长双 SSOT 和旧 schema 生命周期 | 不保留 wrapper；整体 revert 是唯一回滚 |
| 2026-07-19 | 旧 `adk-intake-workflow` 仍可继续使用 | 读取 Skill 与 references | 包含直接 clone、手改 registry、旧脚本和未实现入口 | 删除并由新的 optional absorption Skill/Workflow 替代 |
| 2026-07-19 | 通用 `skill-creator` quick validator 可直接作为 ADK Skill 最终门禁 | 对新 Skill 运行系统 `quick_validate.py` | validator 拒绝 ADK 扩展 frontmatter 中的 version/triggers/non_triggers/inputs/outputs/constraints | 不削弱 ADK 元数据；保留此负结果，使用 ADK strict、metadata、routing 和 optional-install 门禁作为本仓权威验证 |
| 2026-07-19 | `ruff` 可作为本轮 Python 静态门禁 | `rtk ruff check tools/codex_assets/practice_intake.py tools/codex_assets/reference_repository.py` | 环境未安装 ruff，命令无法启动 | 记录 not-run；改用 AST parse、ShellCheck、定向/全量测试和人工 review，不临时引入依赖 |
| 2026-07-19 | clean Git worktree 直接 `release build` 等同 exact-commit build | 在提交后增加未跟踪 verification 文件，再比较 worktree build 与 `git archive <commit>` build | worktree build 包含 3 个未跟踪 evidence 文件，file count 590、SHA 与 exact-commit 的 587 files 不同 | 废弃 worktree artifact；只接受不可变 commit archive 的两次一致构建和对应 rehearsal |
| 2026-07-19 | root full 可在 ADK evidence 未提交且 gitlink/lock 未同步时作为最终 pass | `rtk scripts/check-all.sh --full` | 53/58；三个未同步事实派生出 lock/current/subrepo/evidence/workspace 五项失败 | 保留 pre-sync 负证据；提交 evidence、同步声明后重跑，不弱化门禁 |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk rg ... discover-oss/run-oss/wechat/official` | 0 | 建立旧入口消费者和边界矩阵 | 会话审计；后续固化到根架构文档 | Root | proposal/design |
| `rtk rg ... knowledge/L2-domain/lessons.md` | 0 | `[NEGATIVE]`：文件缺失 | 本文件 | ADK | T1 |
| GitHub/GitLab/Gitee 官方文档检索 | 0 | 三个 forge 的 repository metadata endpoint 与字段已核验；Gitee 空结果风险保留 | `proposal.md`、`design.md` | External source | T1 |
