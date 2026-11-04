# Skills 8.2.3 实现边界与理由

1. 保留 Skill 资产集 58 core + 8 optional，默认 `core` 不增长。`adk-artifact-gating` 与 `adk-pilot-framework` 通过 `team-core` 专用 Profile 显式触达；完整 core 集合由 Profile 覆盖负向测试保证。此设计增加 `team-core` 源码面，但不会增加平台中立 core。
2. 66 个 Skill 的原始描述择优改成 “适用 + 排除”，两份原本已经详细的边界描述保留；专用 frontmatter 触发/非触发列表继续由单一 canonical matcher 解释，不建第二路由器。
3. `adk-data-fetch` 是路由指引而非安装权限；父 Skill 不自动装两个可选子 Skill，使用前必须检查已安装对应子 Skill，缺失则停止。安装计划测试锁定独立选项语义；无需邮箱时绝不隐式增配 IMAP。
4. 仓库维护 Skill 中失效的 `scripts/check.sh`、`scripts/doctor.sh` 换为真实 `scripts/devkit.sh` 入口并加入存在性验证。
5. 移除已迁入 core 的 `optional-skills/adk-planning-execution-loop/references/long-task-recovery.md`，保留 canonical core 参考；并行与 worktree 的相同 reference 保留为独立导出需要的自包含支持资源（不属于兼容 shim）。
6. 保留现有有意义的 Skill Content 明确 override 字段；即使部分字段现在等于推导默认值，其作为意图与权限审查契约的价值大于极少数字节的节省。
7. 八个 Profile ratchet 基于 Git tree 源码字节数更新；不是模型使用、Token 或加载耗时指标。根仓锁仅在受保护版本实际发布后才提升，防止提前 pin 未验候选。

## 证据与停止条件

- 静态 matcher 和 profile 测试通过，只证明确定性代码，不证明 Claude/OpenCode/Codex 实际触发或产出质量。
- 若缺 8.2.3 source-bound 独立审核、受保护 exact-head CI 或不可变 Release，则停止于候选 PR，不得自批、借用 8.2.2 收据或提前更新 Root。
