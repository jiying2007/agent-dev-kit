# Codex Runtime Pilot Runbook

## 适用场景

- 变更已在 `global-dev-kit` 通过本地回归，需要在 `~/.codex` 真实运行目录做最小闭环验证。
- 准备执行“先压实后追踪”的阶段门禁检查。

## 推荐 Agent 链

`application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `verification-before-completion`
- `commit-pr-quality-gate`
- `systematic-debugging`（仅在运行异常时触发）

## 命令模板

```bash
bash ~/.codex/control/scripts/doctor.sh ~/.codex minimal
bash scripts/check-global-codex-health.sh ~/.codex minimal
bash scripts/check-gdk-harden-readiness.sh . --require-pilot --skip-full-suite
```

## 验收门禁

- `doctor` 与 `check-global-codex-health` 必须均为 PASS。
- `check-gdk-harden-readiness` 必须在 `--require-pilot` 条件下通过。
- 验证结论必须包含三联证据：doctor / global health / pilot gate。
- 若任一命令失败，必须记录失败证据并转入 `systematic-debugging`，不得声明可放行。
