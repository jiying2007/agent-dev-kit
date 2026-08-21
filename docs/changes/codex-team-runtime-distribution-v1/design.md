# Design

## Boundaries

```text
private agent-dev-kit source
  -> adk-runtime-bundle/v1
  -> team-codex-assets import plan/apply
  -> team Codex build/plan/apply
  -> member ~/.codex
```

ADK 只负责按 Profile 解析并封装原始 Skill 资产，不执行 Codex 格式转换，也不写 Codex Home。团队仓负责 Codex 版本化 vendor、激活入口、安装 receipt 和回滚。

## Runtime Bundle contract

- 根目录：`adk-runtime-<profile>-<adk-version>/`。
- `bundle-manifest.json`：schema、ADK 版本、manifest digest、Profile、资产清单与逐资产 tree digest。
- `skills/<name>/<skill-version>/`：完整 Skill support tree。
- `checksums.sha256`：bundle manifest 和所有普通文件摘要。
- `LICENSE`：ADK 资产许可证。
- 归档确定性：固定 uid/gid、权限、mtime、排序和 gzip header。
- 安全边界：只允许普通文件/目录；拒绝 symlink、hardlink、special file、重复路径和越界路径。

## Team profile closure

`adk-cross-team-handoff` 从 optional 提升为受 manifest 管理的 core asset，但只由 `team-core` Profile 启用；这不会增加默认 `core` 常驻集合。

## Team repository contract

团队仓使用独立 Python 控制面：

- `bundle plan/apply/rollback`：验证 Runtime Bundle，事务更新 `src/codex-home/vendor/skills` 和 `manifests/skills.json`。
- `build`：生成 vendor 树和 `skills/<name>` 相对 symlink。
- `install plan/apply/rollback`：把 build 事务写入目标 Codex Home。
- `doctor/check`：校验 manifest、版本、摘要、symlink 和 receipt。

所有外部输入先解析为结构化 plan；apply 只接受摘要仍匹配的 plan。目标仓远端只配置，不自动 push。

## Anti-stall

- retry budget：每个失败门禁最多同类重试 2 次，第二次失败必须重审假设。
- staleness threshold：bundle/import/install plan 默认 30 分钟。
- heartbeat：每完成 ADK、团队仓、端到端验证阶段更新 tasks 与证据。
- stop condition：`pass | replan | split | blocked | abort`。
