# Codex Pilot Evidence

- 当前目标链路：`agent-dev-kit -> ~/codex -> ~/.codex`
- 历史直接安装到 `~/.codex` 的试跑记录已移除，不再作为生产验收依据。

## 1. 验收范围

生产 pilot 只认可三类证据：

1. `agent-dev-kit` 本仓验证通过。
2. handoff 产物符合 `~/codex` 源资产与 manifest fragment 规范。
3. `~/codex` build/doctor/apply dry-run 与 `~/.codex` 健康检查通过。

## 2. 标准命令

```bash
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh validate --strict"
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh test"
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh convert --target codex --profile personal-core --extra-profile release-hardening --with-optional-skill adk-planning-execution-loop --with-optional-skill adk-skill-composition-governance --with-optional-skill adk-security-supply-chain --with-optional-skill adk-cross-team-handoff --codex-profile team-collab --out ../reports/adk-codex-handoff --clean"
rtk bash -lc "cd agent-dev-kit && bash scripts/devkit.sh codex-handoff --codex-root ~/codex"
rtk bash -lc "cd ~/codex && rtk bash scripts/build.sh --profile team-collab"
rtk bash -lc "cd ~/codex && rtk bash scripts/apply.sh --profile team-collab --dry-run"
rtk ../scripts/check-global-codex-health.sh ~/.codex minimal
```

## 3. 必备证据

- `manifest-fragments/agents.json`
- `manifest-fragments/skills.json`
- `manifest-fragments/workflows.json`
- `manifest-fragments/mcp_servers.json`
- `manifest-fragments/change_sets.json`
- `~/codex` build 输出
- `~/codex` apply dry-run 输出
- `~/.codex` health 输出

## 4. 阻断条件

- 直接使用 adk install 写入 `~/.codex`。
- handoff 缺少任一 manifest fragment。
- `~/codex` 与 handoff fragment 合并后 profile 解析失败。
- apply dry-run 或 global health 失败且无修复记录。
