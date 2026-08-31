# 负结果记录：remove-external-runtime-compat

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-08-31 | 只修改 Skill 文本、不提升版本即可导入团队 Bundle | `rtk bash scripts/team-assets.sh bundle plan ...` | 拒绝：同版本 `adk-parallel-agent-governance/1.4.0` 内容不同 | Runtime Bundle 以版本化 vendor 路径为不可变身份；行为或内容变化必须提升 Skill 版本 |
| 2026-08-31 | 存在 `tests/test_manifest_mirror.sh` 可直接验证 JSON/YAML 镜像 | 运行该路径 | 命令不存在，退出 127 | 使用 `devkit validate --strict` 和完整 manifest/profile 回归作为真实入口 |
| 2026-08-31 | 含“工作树”的旧外部 review 名称会自然选择 review primary | `devkit.sh match --text ...` | 初始误路由到 `adk-worktree-governance` | 增加 `review反馈核验` 高特异度路由语料和全局回归，审查对象描述不再抢占 primary |
| 2026-08-31 | 未提交删除旧矩阵/脚本可直接进入只读 index-bound parity | Python 3.11/3.12 full parity | 初始 65/67；外部仓名进入 active change docs，且 index inventory 把 4 个删除路径判 missing | change 文档改为中性外部兼容术语；旧路径改为 fail-closed retired tombstone，生产调用全部移除 |
| 2026-08-31 | 根仓 L4 required checks 可全部通过 | root `tests/run_all.sh --fail-fast` 与 `check-all --quick --working-tree` | 被现有 Codex smoke identity 过期和 Claude Code owner attestation 缺失阻断；quick 为 54/55 | 属于既有产品状态证据，不改写或伪造；本轮定向 runtime/routing/target checks 独立通过 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash scripts/team-assets.sh bundle plan ...` | 1 | 同版本内容漂移被拒绝，促使提升 Skill 版本 | terminal output | Runtime Bundle | versioned vendor identity |
| `rtk bash agent-dev-kit/scripts/run-local-ci-parity.sh --python all --mode full`（首次） | 1 | 两个 Python 层均复现 active docs/index inventory 问题 | terminal output | Release Gate | negative path |
| `rtk bash tests/run_all.sh --fail-fast`（根仓） | 1 | 现有产品证据阻断，非本轮 runtime compatibility 改动 | terminal output | Workspace Gate | existing current-status evidence |
