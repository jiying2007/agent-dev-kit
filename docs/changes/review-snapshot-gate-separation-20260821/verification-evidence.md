# Verification Evidence

| Command | Exit | Result | Layer |
|---|---:|---|---|
| `rtk scripts/devkit.sh validate --quick` | 0 | ADK quick validation passed；Python 3.8.10 仅作为开发证据 | Skill |
| `rtk tests/test_skill_sop_quality.sh` | 1 | 新增契约断言通过，后续被三个既有 source_ref 审查到期项阻断 | Skill |
| `rtk tests/run_all.sh --fail-fast` | 1 | `test_validate` 被相同既有 source_ref 到期项阻断 | Workflow |
| `rtk bash scripts/check-skills.sh`（下游） | 0 | 64 skills，0 errors，0 warnings | Skill |
| `rtk bash scripts/check.sh --no-build --plan build/apply-plan.json`（下游） | 0 | 162 tests 和 5 profiles smoke 通过，live 无 drift | Workflow |
| `rtk bash tests/test_asset_content_quality.sh` | 0 | `adk-code-review-loop` 标准 Commands/Evidence Template 章节通过 | Skill |

## Gate decision

本 change 的新增确定性契约、下游导入和 live 投影已通过。ADK 上游完整回归仍受无关的 source_ref 到期基线阻断，因此不得把该命令表述为全量通过；未通过放宽门禁规避。
