# 验证证据：lifecycle-operation-contract-gates-v1

## 行为对比

输入：一个外部请求启动异步操作、持有共享资源，并可能被取消、超时或迟到完成影响的变更。

- 改动前：接口、审查和完成 skill 分别提及部分风险，但没有同一份 owner/state/event 基线；审查可能把语义改变当普通补丁继续处理。
- 改动后：接口设计在适用时要求生命周期操作契约；审查把改变 owner、状态、可见性或终止语义的 finding 标为 `design-change`；完成验证要求契约、owner、终止路径和真实环境边界。普通同步接口可显式标记 `not_applicable`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk git diff --check` | 0 | 无空白错误 | command output | Source | 全部本次改动 |
| `rtk bash tests/test_skill_sop_quality.sh` | 0 | 生命周期契约文本断言与 strict 子校验通过 | command output | Skill | 三个 core skill |
| `rtk bash tests/test_skill_content.sh` | 0 | 448 项通过；三个入口均未超过 140 行 | command output | Skill | SKILL.md 入口约束 |
| `rtk bash scripts/devkit.sh validate --quick` | 0 | quick 资产验证通过 | command output | ADK | core 资产 |
| `rtk bash scripts/devkit.sh validate --strict` | 0 | strict 资产验证通过；Python 3.8 仅 development-only | command output | ADK | core 资产 |
| `rtk bash tests/run_all.sh` | 0 | 68/68 通过 | command output | Test | 完整回归 |

## 风险与回退

- 风险：不适用的普通接口被误套入生命周期流程。
- 缓解：三处均提供条件性适用或 `not_applicable` 路径。
- 回退：回退本 change 涉及的三个 skill、reference、SOP 断言与变更工件；不涉及 manifest、运行时配置、权限或数据迁移。
