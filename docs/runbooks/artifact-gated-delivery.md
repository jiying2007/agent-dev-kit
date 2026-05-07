# Artifact-Gated Delivery Runbook

## 1. 场景适用

- 变更涉及共享契约、发布链路或跨角色交接。
- 需要统一产物标签和门禁结果，避免“口头完成”。

## 2. 推荐能力组合

- Profile：`core + adk-artifact-gated-lite`
- Optional Skill：`adk-artifact-gated-lite`
- 必备技能：`adk-verification-before-completion`、`adk-commit-pr-quality-gate`

## 3. 执行步骤

1. 安装能力组合：
   ```bash
   bash scripts/devkit.sh install --tool codex --profile core --extra-profile adk-artifact-gated-lite --with-optional-skill adk-artifact-gated-lite
   ```
2. 创建变更工件并进入 `propose -> apply`。
3. 在变更工件中补齐三类标签：
   - `[artifact:ImplementationPlan]`
   - `[artifact:ReviewReport]`
   - `[artifact:TestReport]`
4. 执行 `verify`，记录真实命令输出。
5. 执行 `review`，确保与标签化结论一致后再归档（`workflow.sh` 会自动校验一致性）。

## 4. 最小标签模板

```md
[artifact:ImplementationPlan]
status: READY
owner: <agent>
scope:
- <范围>
handoff_to:
- <next-owner>

[artifact:ReviewReport]
status: PASS
verdict: pass | needs-fix

[artifact:TestReport]
status: PASS
tests_run:
- <command + result>
```

## 5. 失败与升级

- 缺失标签或证据：结论必须 `needs-fix`，禁止归档。
- 发现共享契约影响未评估：升级到架构评审再继续。
