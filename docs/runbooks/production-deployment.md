# Production Deployment Runbook

## 目标

把 gdk 安装到全局 `~/.codex`，并保留备份、安装报告、健康检查和回滚路径。

## 推荐命令

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh install --tool codex --target ~/.codex --mode copy --profile personal-core --extra-profile release-hardening --backup --install-report reports/gdk-install-report.md
bash ../scripts/check-global-codex-health.sh ~/.codex minimal
bash ../scripts/check-gdk-harden-readiness.sh .. --require-pilot
```

## 部署纪律

- 生产安装使用 `copy`，避免工作区变动影响运行目录。
- 安装前启用 `--backup`。
- 安装后必须生成 install report。
- 若健康检查失败，回滚到安装报告记录的 backup 路径。

## 验收门禁

- `validate --strict` 通过。
- `check-global-codex-health` 通过。
- `check-gdk-harden-readiness --require-pilot` 通过。
