# Session State：agent-ecosystem-standards-hardening

## 当前检查点

- Phase：verified
- 已完成：来源复核、六类 manifests、checker、正负 fixtures、报告/台账、strict/quick/full regression。
- 当前动作：交付；不 commit、不 push、不 apply。
- 下一检查点：若用户授权提交，先复核 diff，再运行 commit-ready；提交后根仓 strict subrepo-state 可恢复为 pass。

## 恢复参数

- retry budget：同一失败最多 2 次修复；第 3 次仍相同则停下并记录 blocker。
- staleness threshold：来源 metadata 到 `expires_at` 后必须重新复核；本次测试禁止联网刷新。
- heartbeat：每完成 manifests、checker/fixtures、docs、verification 任一阶段即更新 tasks/evidence。
- stop conditions：意外启用 runtime；需要外部写权限；旧测试出现无法解释的回归；发现 blocker/major 未闭环。

## 恢复入口

1. 查看 `state.yaml`、`tasks.md`、`negative-results.md`。
2. 运行 `rtk scripts/check-agent-ecosystem-standards.sh --summary-json`。
3. 从首个失败 contract/fixture 继续，不重复已验证来源调研。

## 明确排除

- 不触碰 dirty 参考子仓。
- 不执行 commit/push/apply。
- 不安装或启动 Agent Skills、ACP、A2A、MCP Registry、gh-aw 或 OTel 组件。
