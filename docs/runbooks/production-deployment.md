# Production Deployment Runbook

## 目标

把 adk 交接到 `~/codex` 声明式资产仓库，再由 `~/codex` apply 到全局 `~/.codex`，并保留导出报告、apply plan、健康检查和回滚路径。

## 推荐命令

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh convert --target codex --profile personal-core --extra-profile release-hardening --with-optional-skill adk-planning-execution-loop --with-optional-skill adk-skill-composition-governance --with-optional-skill adk-security-supply-chain --with-optional-skill adk-cross-team-handoff --codex-profile team-collab --out ../reports/adk-codex-handoff --clean
bash scripts/devkit.sh codex-handoff --codex-root ~/codex
cd ~/codex && rtk bash scripts/build.sh --profile team-collab
cd ~/codex && rtk bash scripts/plan.sh --target ~/.codex --output build/apply-plan.json
cd ~/codex && rtk bash scripts/apply.sh --profile team-collab --dry-run
bash ../scripts/check-global-codex-health.sh ~/.codex minimal
bash ../scripts/check-adk-harden-readiness.sh .. --require-pilot
```

## 部署纪律

- adk 不直接写入 `~/.codex`；`../reports/adk-codex-handoff` 是符合 `~/codex` 规范的交接目录。
- handoff 必须包含 `src/codex-home/vendor/...` 和 `manifest-fragments/*.json`；进入生产前先在 `~/codex` 中合并源资产与 manifest 条目，再执行 build/doctor/apply。
- 正式 apply 前先生成 apply plan 并 dry-run。
- 不覆盖 `~/.codex/AGENTS.md`；该文件由 `~/codex` 源资产维护，详见 `docs/codex-agents-integration.md`。
- 若健康检查失败，使用 `~/codex` apply plan 或 backup 回滚。

## 验收门禁

- `validate --strict` 通过。
- `devkit.sh codex-handoff --codex-root ~/codex` 通过。
- `~/codex/scripts/doctor.sh --scope all` 通过。
- `~/codex/scripts/apply.sh --dry-run` 通过；正式发布时保留 apply plan。
- `check-global-codex-health` 通过。
- `check-adk-harden-readiness --require-pilot` 通过。
