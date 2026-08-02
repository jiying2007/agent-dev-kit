# 需求基线：token-context-governance-v2

## R1：预算余量

- per-layer 与 cumulative `AGENTS.md` 保留 hard limit，并新增 85% soft warning。
- summary 同时输出 bytes、估算 token、warning/hard limit 与 headroom。
- global/root 入口应回落到 soft warning 以内，细节下沉到既有文档。

## R2：可执行 task-cost

- 提供确定性 CLI 生成 `micro | standard | complex | high-risk` receipt。
- receipt 只保存 task SHA256、显式风险信号和预算，不保存任务正文。
- `micro` 必须为 no-skill/no-Hub；`standard` 最多一个 primary；高风险不得降级原文和 full gate。

## R3：双模式工作树门禁

- release 模式继续要求 strict ADK clean state。
- 显式 working-tree 模式允许 ADK dirty，但必须输出 HEAD、状态/diff fingerprint，且整轮验证前后 fingerprint 一致。
- working-tree 模式不得产生可发布、可提交或 release-clean 声明。

## R4：Codex plan v3

- plan schema 升级为 v3，build receipt 与 target precondition receipt 均为必需。
- target receipt 覆盖 mutation 与 keep 路径；keep 漂移时 fail closed。
- no-op/already-applied 仍需验证目录和 keep precondition。

## R5：显式 lazy activation

- token-lean workflow 必须区分 resident、lazy 与 fallback Skill。
- governance 检查确保三类无重复、全部属于 workflow、resident 与 profile 实际激活一致。
- skill-search summary 显示 activation mode，domain 专属能力继续受路由抑制。

## R6：同轮证据复用

- smoke/full 都建立 PID、process start、root、workspace fingerprint 和 producer hash 绑定的 receipt。
- evidence bundle 只复用同轮完整 PASS 输出；任一校验失败真实重跑。
- smoke 保持覆盖不变，并记录复用 consumer/producer。

## R7：Hub 有界输出与 context receipt

- capture 增加不超过 2 KiB 的 `--summary-json`，完整 writes 只在 `--json` 输出。
- context 可显式使用 cache receipt；receipt 不保存 query 正文，并绑定 workspace HEAD、Hub registry 与选中原文 hash。
- 任一签名或原文变化均重新装配，不使用 stale receipt。

## R8：Hub review throughput

- review batch packet 输出 overdue/due-soon/missing-date、domain/owner 聚合和 bounded batch 建议。
- 只生成优先级与人工操作包，不自动填写 human review 或改变 lifecycle。

## R9：跨仓 release bundle

- 生成有界 JSON，记录四仓 HEAD、dirty fingerprint、Codex plan、Hub candidate 和验证证据 hash。
- bundle 不保存 diff 正文、prompt、query、日志、凭证，也不执行提交或发布。

## 验收

- task-cost 正负测试、预算 soft/hard 测试、双模式 dirty/stale 测试通过。
- Codex unit/governance/build/plan/apply/check 通过，旧 v2 plan 被拒绝。
- root smoke 有真实 reuse，耗时较 v1 下降；无法达到 20 秒时保留 slowest 证据。
- Hub context/capture/review queue 定向测试与完整 pytest、knowledge-check 通过。
- source-to-live 和跨仓 bundle 均可复跑；Hub 只创建 reviewing candidate。
