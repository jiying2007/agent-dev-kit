# Knowledge Compile Model Runbook

## 目标

`llm-wiki-knowledge-compile-v1` 将外部 LLM Wiki 模式收敛为 ADK 的知识归档能力：保留不可变原始材料，维护可读综合页，并用 schema 固化命名、链接、frontmatter 和维护规则。

综合页用于降低重复阅读成本，不是原始证据。任何结论、经验或记忆候选在晋升前都必须能回退到 `raw_sources` 或等价原始证据。

## 三层模型

| Layer | 用途 | 边界 |
|---|---|---|
| `raw_sources` | 保存原文、日志、网页摘录、命令输出、调研材料或本地文件引用 | Agent 不得改写、覆盖或把摘要写回原始材料 |
| `maintained_wiki` | 维护主题页、概念页、索引页和跨引用，承载人工审查后的综合知识 | 必须引用 raw source 或 raw evidence path；不得作为 primary evidence |
| `schema` | 定义目录、文件命名、frontmatter、链接规则、stale 标记和 lint 规则 | schema 变更必须说明兼容影响和迁移策略 |

推荐目录可以由项目自行映射，但语义必须保持：

```text
docs/archive/<topic>/raw_sources/
docs/archive/<topic>/wiki/
docs/archive/<topic>/schema/
```

## 操作：ingest

`ingest` 负责把新材料登记为可审计来源，并生成或更新待审查综合页。

1. 为每个输入记录 `source_url_or_local_path`、`retrieved_at`、`review_status`、`expires_at`、来源类型和脱敏状态。
2. 将原始材料放入 `raw_sources`，或登记只读外部 URL / 本地路径；不得编辑原始材料。
3. 创建或更新 `maintained_wiki` 页面时，必须填写 `raw_source_path`、`wiki_page_path`、`schema_path` 和 `raw_fallback`。
4. 新 synthesis 只作为候选内容写入综合页，涉及默认行为、记忆晋升或规则提升时必须走 owner review。
5. 创建新主题页前必须填写 `duplicate_concept_check`：先查索引、列出候选匹配页，并给出 `update-existing` / `create-new` / `reference-only` 结论。
6. 若发现已有同名实体、概念或主题页，优先更新现有页并追加 `change_log`，不要创建重复页面。

## 操作：query

`query` 负责按需读取知识，而不是把 wiki 全量注入上下文。

1. 先读索引、schema 或主题摘要，确定相关页面和 raw fallback。
2. 普通低风险问题可引用 `maintained_wiki` 的 summary，但回答中必须保留来源路径。
3. 高风险、争议、过期或需要精确引用的结论必须回读 `raw_sources`。
4. 若查询产生新的有价值综合结论，只能作为待审查变更追加到 `change_log` 或候选区。
5. 查询结果不得把综合页当作唯一证据，也不得覆盖 stale claim 的原始记录。

## 操作：lint

`lint` 负责发现知识库漂移和证据断链。

必须检查：

- `raw_source_path`
- `wiki_page_path`
- `schema_path`
- `source_url_or_local_path`
- `retrieved_at`
- `review_status`
- `expires_at`
- `summary`
- `cross_references`
- `duplicate_concept_check`
- `stale_claims`
- `raw_fallback`
- `change_log`

质量门禁：

- raw sources 保持不可变，Agent 不改写原始材料。
- wiki 页面引用 source material 或 raw evidence paths。
- schema 定义 naming、frontmatter、links 和 maintenance rules。
- lint 标记 stale claims、weak links、orphan pages 和 unresolved questions。
- lint 标记 duplicate concept pages；缺少 `duplicate_concept_check` 的新综合页不得晋升。
- 外部来源必须有 `retrieved_at`、`review_status`、`expires_at`，过期来源必须回读 raw source 或重新采集。
- 来自 compiled wiki 的查询新结论，必须审查后才能写回 wiki。

## Note 模板

知识编译条目使用 `templates/memory/knowledge-compile-note.md`。字段缺失时不得晋升为长期记忆、项目规则或默认 skill 行为。

## 与记忆治理的关系

知识编译页属于 retrievable memory 或 archive synthesis，不属于 resident memory。它可以帮助定位证据和总结关系，但不能替代 `templates/memory/memory-candidate.md` 的写入准入、风险分级、`last_verified` 和 `next_review_by`。

## 与 token context 的关系

读取顺序默认是 schema/index -> maintained wiki -> raw sources。出现低置信度、高风险、过期断言、引用缺失、schema 冲突或交付争议时，必须回退原始材料。

## 验证

```bash
rtk bash scripts/check-knowledge-compile-model.sh
```
