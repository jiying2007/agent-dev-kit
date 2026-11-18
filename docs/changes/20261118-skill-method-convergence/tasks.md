# Skill 方法沉淀：执行与验证

| 阶段 | 内容 | 验证与状态依据 |
|---|---|---|
| 1 | 统一来源决策、七字段方法、术语和维护入口 | 本 change 的实际 diff；独立 Spec/Quality review |
| 2 | 对三类重点能力复用已有开发任务和失败边界 | 原 skill-content/quality/efficiency 检查的本候选 CI 结果 |
| 3 | 通过共享规范覆盖 65 个 Skill，保留 core/optional 与导出边界 | 原全清单触发、内容、portfolio、consumer 检查的本候选 CI 结果 |
| 4 | 受保护合并、不可变发行与 Root exact-source 消费 | GitHub PR、main workflow、release 和 Root consumer workflow 的原始回执 |

## 证据规则与当前环境

当前编辑环境是源文件快照，不是完整 checkout，且无真实 `rtk`；未在此环境执行项目测试，不能声明本地回归通过。验证沿现有 GitHub Actions 执行；PR 检查、main 检查、发行和消费各自绑定实际提交。CI 启动或静态审查不代表验证通过。

可在具备原工具链的完整 checkout 执行 `rtk scripts/devkit.sh validate --strict`、`rtk tests/test_skill_content.sh`、`rtk tests/test_skill_trigger_matrix.sh`、`rtk tests/run_all.sh` 和 `rtk scripts/devkit.sh release check`。这里列的是恢复入口，是否通过以实际回执为准。

执行结果保留在关联 PR 的独立审查及 Actions 原件，不把本任务表作为第二结果台账。出现失败按原流程记录原因和修复；保留原失败，不选择性删除或扩大预算。真实模型/宿主/现场验证均未执行，相关效果保持未测。
