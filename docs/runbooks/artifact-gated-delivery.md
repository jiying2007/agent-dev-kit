# Artifact-Gated Delivery Runbook

## 1. 场景适用

- 变更涉及共享契约、发布链路或跨角色交接。
- 需要统一产物标签和门禁结果，避免"口头完成"。

## 2. 推荐能力组合

- Profile：`core`
- Skill：`adk-artifact-gating`
- 必备技能：`adk-verification-before-completion`、`adk-commit-pr-quality-gate`

## 3. 执行步骤

1. 在临时目标验证核心能力：
   ```bash
   bash scripts/devkit.sh install --tool codex --target /tmp/adk-codex-target --profile core
   ```
2. 创建变更工件并进入 `propose -> apply`。
3. 在变更工件中补齐三类标签：
   - `[artifact:ImplementationPlan]`
   - `[artifact:ReviewReport]`
   - `[artifact:TestReport]`
4. 执行 `verify`，记录真实命令输出。
5. 执行 `review`，确保与标签化结论一致后再归档。

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

## 6. 边界

`adk-artifact-gating` 是唯一保留的 artifact 门禁入口；旧 lite optional skill 和外部参考仓全文协议已移除，避免高风险交付出现双轨规则。
