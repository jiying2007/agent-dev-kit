# 负结果

## 已验证的负结果

| 假设 | 结果 | 处置 |
|---|---|---|
| 旧 plan 可直接复用 | fail-closed | 重建 plan 与 dry-run |

- 从 `llm_agent` cwd 调用 `~/codex/scripts/apply.sh` 时发生同名 `tools` 包解析冲突；改为在 `~/codex` cwd 执行，未对 live 产生该次失败的写入。
- 使用旧 plan 重试 apply 被 managed-state precondition 拒绝；按 fail-closed 规则重建 build、plan 和 dry-run 后才 apply。
- 单纯依赖 `--prune-stale` 无法移除不在历史 managed-files 中的 Superpowers 残留；改为受审查的 `retired_live_paths`，删除仍由备份绑定 plan 执行。

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| old plan apply | 1 | managed-state precondition rejected stale plan | terminal | Runtime | negative result |
