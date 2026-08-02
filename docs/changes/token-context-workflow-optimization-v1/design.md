# 设计说明：token-context-workflow-optimization-v1

## 架构影响

- D1：建立四级 task-cost contract。路由先判任务/仓库/domain，再进行 Skill 词法匹配；
  `no-skill` 是 micro 任务合法终态。
- D2：固定上下文采用 hierarchical cumulative budget。各仓保留自己的入口门禁，
  根仓额外验证 Codex global + root + ADK local 的累计值。
- D3：`token-lean` 只常驻通用路由、需求、调试、验证和 Token 治理；协作、Git
  收尾、资产治理、嵌入式能力仍在 trusted inventory 延迟加载。
- D4：Hub `context` 作为单一默认预检入口，增加显式 project hint 和 2 KiB summary
  projection；telemetry 默认关闭、显式 opt-in，写失败不污染业务结果。
- D5：usage dashboard 对 SQLite schema 做 capability detection，缺失 goals 表时返回
  `goals_available=false`，线程/token 数据继续可用。
- D6：门禁复用沿用已有 fail-closed same-run evidence；Codex build/plan receipt 绑定
  source/profile/build/target mutation paths，并区分 ready/already-applied/stale。
- D7：所有成功输出使用 bounded summary；完整输出只在显式 `--json/--verbose` 或
  失败回退时读取。

## 数据与配置影响

- `profiles.json:context_budget` 新增累计 AGENTS、默认候选数和 summary 字节预算。
- Skill manifest 增加/复用 domain/profile metadata；不删除 skill 实体。
- Hub context CLI 新增显式 project/scope 选项，summary contract 保持 schema versioned。
- Codex receipt 为可重建 build evidence，不作为 release 或跨签名缓存。
- usage JSON 增加 availability 字段；旧 consumer 可忽略新增字段。

## 兼容性与迁移方案

- 显式 `--limit`、`--json`、`team-collab` 和 full gate 语义保持不变。
- profile 缩减后从新线程生效；旧会话不声明 catalog 已刷新。
- receipt 缺失、过期、hash/target/profile 不匹配时执行真实命令。
- Hub 未传 route hint 时沿用 cwd/query 路由；显式 hint 只缩小范围，不放宽权限。
- 任一路由准确率或高风险验证覆盖退化，按文件级 patch 回滚对应 D 项。

## 验证策略

- ADK：change apply/verify、token budget、strict validate、相关 contract tests。
- Codex：usage schema fixture、skill catalog/routing、doctor、governance、build/plan/apply
  dry-run、完整 `check.sh`。
- Hub：context/search 定向 pytest、knowledge-check summary、retrieval benchmark/metrics。
- 根仓：token budget、doc/AGENTS、check-all contract、smoke timing 和 runtime health。
- 终态：source-to-live build/doctor/plan/dry-run/apply、routing、full check、final-ready。

## 安全与回退

- 不复用失败、跨 PID、跨 root、跨 source hash 或跨 target 的证据。
- 不自动写 Hub active/memory，不保存 raw prompt/query/log。
- 不直接修改 `~/.codex`；只由审核后的 apply plan 写入并保留 rollback evidence。
- 外部仓发现 dirty 重叠时暂停该阶段，不覆盖用户改动。
