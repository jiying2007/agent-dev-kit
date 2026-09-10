# 负结果记录：lifecycle-operation-contract-gates-v1

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-09-04 | 新增 SOP 断言可直接通过 | `tests/test_skill_sop_quality.sh` | 首次因断言术语与标题不一致失败 | 统一为 `受控生命周期契约` 后重跑 |
| 2026-09-04 | P0 接口契约 skill 已满足反合理化测试 | `tests/test_anti_rationalization.sh` | 现有源文件缺少该章节 | 补充最小通用章节，不将此缺口归因于领域逻辑 |
| 2026-09-04 | check item 可携带解释文本 | `scripts/devkit.sh verify --change lifecycle-operation-contract-gates-v1` | governance 无法匹配精确 checklist 项 | 将解释移为独立子项后重试 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash tests/test_skill_sop_quality.sh`（首次） | 1 | 新增断言术语与 skill 标题不一致 | 本文件已验证的负结果 | Skill | SOP 文本契约 |
| `rtk bash tests/test_anti_rationalization.sh`（首次） | 1 | 既有 P0 接口契约 skill 缺少反合理化章节 | 本文件已验证的负结果 | Skill | P0 质量基线 |
| `rtk bash tests/run_all.sh` | 0 | 68/68 通过 | `verification-evidence.md` | Test | core skill 回归 |
| `rtk bash scripts/devkit.sh verify --change lifecycle-operation-contract-gates-v1`（首次） | 1 | fail-closed：checklist 精确项缺失 | `verify-report.md` | Workflow | change governance |
