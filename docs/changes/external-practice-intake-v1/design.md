# 设计说明：external-practice-intake-v1

## 架构边界

`llm_agent` 是唯一 intake 控制面，负责 provider、候选、review queue、周期证据和批准前治理；`agent-dev-kit` 只保存平台中立的吸收方法、角色、Workflow、验证门禁与已批准实现。Knowledge Hub 只保存 reviewing/validated 决策与长期证据，不接受 raw response、token、正文或 cache。

```text
forge APIs / official manifests / WeChat catalogs / manual URLs
                         |
                 provider adapters
                         |
          external-practice-candidate.v1 JSONL
                         |
        schema + trust + freshness + safety + dedup
                         |
                 review queue (no decision)
                         |
             independent owner decision
                 /                 \
       repository lifecycle      ADK change artifact
                                      |
                       implement -> verify -> pilot -> release -> retire
```

## 根仓实现

### 单一入口

- `scripts/practice-intake.sh`：只定位根目录、注入 `PYTHONPATH` 并转发到 `tools.codex_assets.practice_intake`。
- Python CLI 子命令：
  - `collect`：单 provider 或人工输入生成 candidate ledger 与 transport evidence。
  - `check`：严格验证 source policy、candidate ledger、cycle plan 或 decision ledger。
  - `queue`：把未决候选和 provider degraded 状态生成为 review queue。
  - `cycle`：按显式 plan 顺序执行 collect/check/queue，写 JSON/Markdown evidence；绝不执行 decision 或 apply。
  - `recommend`：基于固定规则给出 `agent|skill|workflow|script|manifest|runbook|observe` 建议，不生成资产。

### Provider 合同

| provider | transport | 输入/接口 | 边界 |
|---|---|---|---|
| `github` | HTTPS metadata | `GET /search/repositories`，fixture 可替代 | 公开元数据；token 仅提升 rate limit |
| `gitlab` | HTTPS metadata | `GET /api/v4/projects?search=...`，公开项目可匿名 | `topics` 替代 deprecated `tag_list`；license 缺失为 unknown |
| `gitee` | HTTPS metadata | `GET /api/v5/search/repositories`，fixture 可替代 | 空响应为 degraded；token 作为 query 参数时不得进入 evidence/log |
| `openai-official` | local manifest | ADK `official_docs_freshness_gates.json` 中 OpenAI records | 不联网、不复制正文 |
| `anthropic-official` | local manifest | 同一 manifest 中 Anthropic records | 不联网、不激活 Claude runtime |
| `wechat` | local catalog | `catalog.jsonl`，要求 `body_persisted=false` | 不抓正文、不绕过访问控制 |
| `manual` | URL/JSONL | GitHub/GitLab/Gitee/官方 URL | ledger-only、review-required |

所有网络 URL 必须匹配 source policy 的 exact scheme/host/path prefix。自定义企业 GitLab endpoint 不在 v1 默认 allowlist；后续必须通过独立 policy change 加入，不能靠 CLI 任意 URL 绕过。

## 数据合同

### Candidate

必需字段：

- `schema_version`、`candidate_id`、`source_id`、`provider`、`source_type`
- `authority_level`、`title`、`canonical_url`
- `repository`、`revision`、`published_at`、`last_activity_at`
- `retrieved_at`、`review_after`、`expires_at`
- `license`、`topics`、`summary`、`content_sha256`
- `transport`、`body_persisted`、`trust_status`、`review_status`
- `risk_flags`、`evidence_refs`、`asset_recommendation`
- `auto_actions`

固定不变量：

- `review_status=review-required`
- `body_persisted=false`
- `auto_actions=[]`
- `transport in {metadata-only, ledger-only}`
- `candidate_id=sha256(provider + canonical_url + stable revision/content hash)` 的短前缀，排序与重复采集稳定
- 未知 license、revision、published time 必须显式 `unknown`/`null`，不得推测

### Decision

decision 是独立 JSONL，不修改 candidate：`candidate_id`、`decision`、`owner`、`reviewed_at`、`rationale`、`target`、`evidence_refs`。允许 `ADOPT|MERGE|ENHANCE|OBSERVE|REJECT`；只有 owner、日期、理由、证据齐全才有效。collector/cycle 永远不生成 approved decision。

### Cycle evidence

记录 source job、fixture/live、请求 host/path（不含 query token）、状态、候选数、去重数、degraded/error、输出 hash、耗时和边界声明。不能保存响应正文或凭证。

## 安全与性能

- 只用 Python 标准库；禁止 shell 调用、clone、动态 import、模板执行和第三方插件。
- HTTPS、allowlist、15 秒超时、4 MiB 响应上限、每 job 100、每 cycle 500、摘要 1000 字符、topic 50 个。
- 原子写入；拒绝 symlink 输出；输出父目录必须存在于 workspace、`/tmp` 或用户显式路径且不能覆盖输入。
- token env 名称来自 policy；值只进入 header/query request，不进入 exception、JSON、Markdown 或 telemetry。
- JSON 必须是 object/list 预期形态；控制字符、非字符串 URL、非整数计数、未知 provider fail closed。
- 同 URL 跨来源去重时保留最高 authority，但 evidence/source sightings 合并；不以 star 数决定采纳。

## ADK 资产

- 删除 `skills/adk-intake-workflow/` 及 manifest/profile/catalog 引用。
- 新增 optional Skill `adk-external-practice-absorption`：触发外部实践吸收，强制 source/duplicate/license/security/architecture/eval/retirement gate。
- 新增 Agent `external-practice-curator`：只读与报告角色，不能实现、批准或发布自身候选。
- 新增 Workflow `external-practice-absorption`：`discover -> normalize -> triage -> decide -> propose -> implement -> verify -> pilot -> publish -> review/retire`；在 decide/propose/publish 有人工门。
- 不新增每来源 Agent，不把 root collector 打包进 ADK，不启用外部 MCP/runtime。

## 硬切换与残留定义

删除 proposal 中列出的旧入口、manifest、发现/queue/WeChat fixtures 与测试。更新根 AGENTS、维护指南、吸收治理、scripts README、runbook、doc-sync/check-all、ADK manifest/catalog/usage。

以下允许保留且不算残留：

- `reports/`、Knowledge Hub archived/reviewing 证据中的历史命令。
- adoption matrix 中过去吸收记录。
- repository registration/removal policy、subrepo lifecycle 和已注册参考仓状态；它们属于批准后生命周期。

增加 `check-practice-intake.sh` 的 active-tree legacy audit：扫描 AGENTS、README、docs、scripts、tests、fixtures、manifests 和 ADK current assets；禁止旧命令、旧 manifest 与旧 Skill 名称，只排除历史 reports/archive/decision provenance。

## 迁移与回滚

- 无兼容期。代码合入即只接受新命令与 schema。
- 旧 candidate ledger 不自动转换；如需复用，必须重新 collect 或显式人工输入并生成新 candidate ID。
- 批准后的 repository lifecycle 只通过 `scripts/onboard-reference-repository.sh` 读取新 candidate + decision；删除 `scripts/onboard-oss-candidate.sh`，未迁移调用立即失败。
- 回滚是整体 revert；不得恢复双写、alias、旧 schema reader 或 warning-only wrapper。

## 验证策略

1. Provider fixtures：GitHub/GitLab/Gitee/official OpenAI/official Anthropic/WeChat/manual 正例。
2. 负例：未知 host/provider、HTTP、malformed response、过大响应、空 Gitee、token redaction、旧 schema、正文持久化、auto action、无 owner decision。
3. 幂等：相同输入两次 ledger SHA 相同（固定 `--as-of`）。
4. Cycle：六 provider 统一输出、queue、evidence 和 hash；任何 job error 非零，degraded 显式可配置是否 gate。
5. ADK：manifest sync、Skill/Agent/Workflow metadata、routing conflict、strict/full regression。
6. Root：practice check、doc sync、agents coverage、quick/full、legacy residue、diff check、final-ready。
