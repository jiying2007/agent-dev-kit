# 八个既有 Skill 的 description-only 近邻消歧及静态元数据门禁 — Negative Results and Evidence Index

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-10-16 | 只改 Skill description 不必同步生成目录 | 初次 PR CI 38899870541 test_catalog | 不成立：docs/agent-skill-catalog.md 生成投影漂移，PR 后续修复后全绿 | 违反正确性或来源体积治理 |
| 2026-10-16 | CI 通过即可宣称真人独立 Review 和真实模型效果 | GitHub PR #199 reviews 与 G21/G22 当前证据合同 | 不成立：无 GitHub 独立 Review，G21/G22 未验收 | 不伪造 owner 或现场 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| PR #199 agent-dev-kit-ci 38900434203 | 0 | 成功；exact PR-head 主线所需检查均通过 | https://github.com/jiying2007/agent-dev-kit/actions/runs/38900434203 | Repository CI | proposal and tests |
| main agent-dev-kit-ci 38901196518 | 0 | 成功；fresh main / promotion evidence | https://github.com/jiying2007/agent-dev-kit/actions/runs/38901196518 | Repository CI | verify-report |
| release v8.0.21 | 0 | Immutable Release 已发布；旧 Tag 不允许被移动 | https://github.com/jiying2007/agent-dev-kit/releases/tag/v8.0.21 | Component Release | source identity |
| GitHub PR #199 independent reviews | not-run | Reviews 为空；必须取得真人独立意见才能 archive | https://github.com/jiying2007/agent-dev-kit/pull/199 | Owner review | checklist |

## Boundary
- metadata 静态词汇检查不等于 Claude/Codex/OpenCode 真实发现或 G21；无独立 PR 审核。
- 未执行的真实模型、原生发现、现场与人工签署均不能被标成成功。
