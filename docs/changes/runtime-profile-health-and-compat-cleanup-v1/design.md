# 设计说明：runtime-profile-health-and-compat-cleanup-v1

## 决策

live health 的资产归属以 live `control/state/managed-files.json` 为主：该文件记录 apply 时的 profile、路径、类型与摘要。health 必须读取 active profile，并要求它等于 managed-files 的 profile；随后以 managed paths 判断 direct/vendor skill 是否为受管资产。

这消除“默认 build 与 live team-collab profile 不同”造成的假阳性，但不放宽安全性：不在 managed-files 的 skill 继续失败，`runtime_footprint` 的 forbidden paths 继续独立失败。

## 变更范围

- `~/codex/tools/codex_assets/core.py`：unmanaged 检测接受受管 path 集合而非默认 build 目录。
- `~/codex/tools/codex_assets/cli.py`：live doctor 校验 active profile、managed profile 和 source profile 输入；新增正反测试。
- `~/codex` manifests/source：删除 Superpowers plugin 的运行时导出声明；参考仓不删除。
- `llm_agent`：health adapter 透传 profile 一致性结果；current status 使用健康/footprint 结果更新 freshness，而非沿用历史 pass。

## 回滚

- Source 修改：回退对应 `~/codex` clean commit，重建 plan。
- Live 修改：只使用 apply 产生的 backup anchor 回滚；不手改 `~/.codex`。
- 若清单格式不兼容，health fail-closed，不把不确定资产标为已受管。
