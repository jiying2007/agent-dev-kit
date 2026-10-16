# 现有路由导出 E0-E3 保守投入等级，调试审查证伪，A/B/A/B 性能证据纪律 — Negative Results and Evidence Index

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-10-16 | 直接增加 Skill 文字无需关注 source/context 预算 | 候选 PR 的 hosted regression 38891334995 与 38892101740 | 不成立：Profile 字节预算和必需元数据门禁失败，最终通过减少冗余文本解决 | 违反正确性或来源体积治理 |
| 2026-10-16 | CI 通过即可宣称真人独立 Review 和真实模型效果 | GitHub PR #198 reviews 与 G21/G22 当前证据合同 | 不成立：无 GitHub 独立 Review，G21/G22 未验收 | 不伪造 owner 或现场 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| PR #198 agent-dev-kit-ci 38892568551 | 0 | 成功；exact PR-head 主线所需检查均通过 | https://github.com/jiying2007/agent-dev-kit/actions/runs/38892568551 | Repository CI | proposal and tests |
| main agent-dev-kit-ci 38893064699 | 0 | 成功；fresh main / promotion evidence | https://github.com/jiying2007/agent-dev-kit/actions/runs/38893064699 | Repository CI | verify-report |
| release v8.0.20 | 0 | Immutable Release 已发布；旧 Tag 不允许被移动 | https://github.com/jiying2007/agent-dev-kit/releases/tag/v8.0.20 | Component Release | source identity |
| GitHub PR #198 independent reviews | not-run | Reviews 为空；必须取得真人独立意见才能 archive | https://github.com/jiying2007/agent-dev-kit/pull/198 | Owner review | checklist |

## Boundary
- E1 只在明确低风险 workspace-only 可推荐；真实 Task/Token 和硬件效果均未实测；独立 review 未签署。
- 未执行的真实模型、原生发现、现场与人工签署均不能被标成成功。
