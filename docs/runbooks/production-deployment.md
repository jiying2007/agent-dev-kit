# Production Deployment Runbook

## 目标

把 adk 安装到全局 `~/.codex`，并保留备份、安装报告、健康检查和回滚路径。

## 推荐命令

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile personal-core --extra-profile release-hardening --with-optional-skill adk-planning-execution-loop --with-optional-skill adk-skill-composition-governance --with-optional-skill adk-security-supply-chain --with-optional-skill adk-cross-team-handoff --with-optional-skill adk-artifact-gated-lite --backup --install-report ../reports/adk-install-report-$(date +%F).md --lock-version 0.3.0
bash ../scripts/check-global-codex-health.sh ~/.codex minimal
bash ../scripts/check-adk-harden-readiness.sh .. --require-pilot
```

## 部署纪律

- 生产安装使用 `copy`，避免工作区变动影响运行目录。
- 安装前启用 `--backup`。
- 安装后必须生成 install report。
- 安装时使用 `--lock-version` 固定 manifest 版本。
- 不覆盖 `~/.codex/AGENTS.md`；该文件只追加 adk 配合规则，详见 `docs/codex-agents-integration.md`。
- 若健康检查失败，回滚到安装报告记录的 backup 路径。

## 验收门禁

- `validate --strict` 通过。
- `check-global-codex-health` 通过。
- `check-adk-harden-readiness --require-pilot` 通过。
