# 既有 matcher 的 20 条目录级候选竞争、否定与弃权回放 — Negative Results and Evidence Index

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-10-16 | 未知请求必须选择某个 Skill | 全目录 20 条语料中未知请求和否定句的 matcher 回放 | 不成立：生产 matcher 返回 abstain 与 deny，不得自动授予写权限 | 违反正确性或来源体积治理 |
| 2026-10-16 | CI 通过即可宣称真人独立 Review 和真实模型效果 | GitHub PR #197 reviews 与 G21/G22 当前证据合同 | 不成立：无 GitHub 独立 Review，G21/G22 未验收 | 不伪造 owner 或现场 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| PR #197 agent-dev-kit-ci 38890289093 | 0 | 成功；exact PR-head 主线所需检查均通过 | https://github.com/jiying2007/agent-dev-kit/actions/runs/38890289093 | Repository CI | proposal and tests |
| main agent-dev-kit-ci 38890800386 | 0 | 成功；fresh main / promotion evidence | https://github.com/jiying2007/agent-dev-kit/actions/runs/38890800386 | Repository CI | verify-report |
| release v8.0.19 | 0 | Immutable Release 已发布；旧 Tag 不允许被移动 | https://github.com/jiying2007/agent-dev-kit/releases/tag/v8.0.19 | Component Release | source identity |
| GitHub PR #197 independent reviews | not-run | Reviews 为空；必须取得真人独立意见才能 archive | https://github.com/jiying2007/agent-dev-kit/pull/197 | Owner review | checklist |

## Boundary
- 没有三方独立 GitHub review；基线为确定性路由测试，不是原生 Skill/模型评估。
- 未执行的真实模型、原生发现、现场与人工签署均不能被标成成功。
