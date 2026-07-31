# Negative Results

## 已验证的负结果

| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-30 | GitHub main revision 可作为 final identity | 比较 candidate revision、final tag 与 tag commit | main `41d9e9...` 与 tag commit 不同 | 采用不可变 tag `2026-07-28` 和 `5f5440...` |
| 2026-07-30 | final 已发布即可声明 compatibility | 检查 owner prerequisites | schema/client-server/auth/rollback 均为 not-run | compatibility claim 和 activation 必须保持 false |
| 2026-07-30 | 可把上游许可证简化为单一许可证 | 复核仓库 license transition evidence | Apache-2.0、MIT、CC-BY-4.0 边界并存 | 只记录 metadata，不复制内容 |
| 2026-07-30 | `runtime_enabled=false` 足以证明新特性禁用 | 检查既有 manifest 字段 | 没有 Tasks/Apps/extensions 独立状态 | 增加 feature enablement 与负 fixture |
| 2026-07-30 | 初始 change 工件已满足门禁 | 运行 change governance | 缺少 checklist，随后又缺必需 section | 先补齐工件，不绕过治理检查 |
| 2026-07-30 | 更新 manifest candidate 和主检查块即可完成 source refresh | 运行 ecosystem/strict 定向门禁 | 17 项失败，checker 仍有三处 RC source/decision 硬编码 | 同步唯一 checker 引用，不保留失真的 RC alias |
| 2026-07-30 | 现有 source decision enum 可表达 owner 的 ENHANCE | 运行 ecosystem test | external pattern checker 只允许 adopt/observe method-only | 增加 `enhance-metadata-only`，仍由 runtime/install fail-closed 约束 |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk scripts/practice-intake.sh check --kind decision --input reports/external-practice-targeted-decisions-2026-07-30.jsonl` | 0 | owner decision schema pass | `reports/external-practice-targeted-decisions-2026-07-30.jsonl` | Governance | owner decision |
| `rtk bash agent-dev-kit/scripts/check-change-governance.sh agent-dev-kit/docs/changes/mcp-2026-final-metadata-refresh-2026-07-30` | 1 | 首次缺 checklist，第二次缺 proposal section | 本文件 | Change | negative result |
| `rtk bash agent-dev-kit/scripts/check-agent-ecosystem-standards.sh --summary-json` | 1 | 17 项 RC source/decision stale-reference 失败 | 本文件 | Manifest | T2 fail-closed-tests |
| `rtk bash agent-dev-kit/tests/test_agent_ecosystem_standards.sh` | 1 | external source decision enum 缺少 ENHANCE metadata-only | 本文件 | Test | T2 fail-closed-tests |
