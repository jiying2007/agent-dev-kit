# 交付清单：adk-v3-1-rc2-target-conformance

- [x] 三个 direct target 使用 versioned contract，状态均为 `experimental`。
- [x] Claude Code/OpenCode Agent 与 Skill 使用原生树；Hermes 仅支持已证实的 Skill 树。
- [x] Agent/Skill frontmatter、permission profile、support directory 和 provenance 可机械验证。
- [x] export/install 共用 renderer，输出路径与内容 hash 一致。
- [x] export manifest v2、install plan v2、receipt v3、旧 receipt rollback 与旧 plan 拒绝已覆盖。
- [x] manifest Draft 2020-12 Schema 由 `jsonschema` 执行并覆盖预期失败。
- [x] OpenAI 与 Anthropic 官方资料使用同一结构化 freshness gate。
- [x] OOD/adversarial、trace/outcome 与 routing ablation 证据已保存。
- [x] CLI cold-start、10x plan、10x I/O 与 peak-memory budget 已保存。
- [x] ADK full 51/51、Ruff、ShellCheck、security、依赖审计和 release check 通过。
- [x] breaking change、迁移和 rollback 路径有文档与演练入口。
- [ ] 真实 Claude Code/OpenCode/Hermes discovery/load/trigger/permission runtime 认证。
- [ ] ADK commit 后同步根仓 gitlink、`adk.lock`、current status 与 Software M5 integrity。
- [ ] 远端 clean-clone CI、Scorecard、artifact attestation 实际运行。
- [ ] 双 runtime campaign、独立仓库、第二操作者和 30 天 field evidence。

未勾选项均为外部执行或发布提升门禁，不影响本地实现已验证结论，但阻止 target 从 `experimental` 提升以及 M4/M5 成熟度声明。

## 治理模板保留项

- [ ] Prompt before/after 对比证据
  - 不适用：本变更未改 Agent/Skill prompt 主体；以 OOD/adversarial route/safety/trace/outcome 回归替代。
- [ ] Evidence Index 命令级字段完整（命令/退出码/结果摘要/证据路径/层级/关联工件）
  - 已在 `negative-results.md` 按六字段记录；保留未勾选表示仍需独立 reviewer 复核。
- [ ] Skill Intake 归属与安装范围结论
  - 不适用：没有引入第三方 Skill；target adapter 属于 ADK core，外部工具仅为 CI 门禁。
- [ ] 收敛结论或阻塞说明
  - 本地实现已收敛；commit/root lock、runtime、remote CI、第二操作者和 field evidence 保持 blocker。
