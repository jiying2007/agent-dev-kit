# Evidence Graph Runbook

Evidence Graph 用内容哈希和受限关系连接 `source → decision → asset → bundle → runtime → trace → outcome → release/rollback → retirement`。

## 边界

- 只保存脱敏 identity、hash、层级、owner、freshness、retention 和有限 outcome metrics。
- 每个节点必须使用 `ref:<sha256>` opaque ref，并绑定 evidence root 内存在的非 symlink 文件；
  `content_sha256 == evidence_ref.sha256 == 实际文件SHA-256`。
- 该文件必须是 `adk-evidence-node-claim/v1` typed envelope，精确绑定 `node_id`、`node_type`、
  `evidence_layer`，再通过 `subject_ref` 绑定另一份脱敏 JSON subject；同一 claim 文件不能复用于多个节点。
- 不保存 prompt、message、raw log、credential、tool payload 或 runtime state。
- graph pass 只证明 provenance 结构完整，不代表 owner approval、release authorization、runtime 或 field 成熟。

## 必需 outcome metrics

- task success / first-pass success
- human interventions
- elapsed time
- input/output token
- tool call count
- wrong-skill / abstain

## 验证

```bash
rtk bash tests/test_evidence_graph.sh
rtk bash -lc 'PYTHONPATH=src python3 -m agent_dev_kit.evidence_graph \
  --contract manifests/evidence_graph_contracts.json \
  --input path/to/sanitized-graph.json \
  --evidence-root path/to/evidence-root \
  --as-of 2026-08-30T23:59:00Z \
  --summary-json'
```

任何 dangling edge、duplicate ID、cycle、未知 edge taxonomy、非法/未绑定 hash、缺失或复用 typed claim、
claim/node identity 不一致、subject 缺失、
未来时间、倒置 expiry、缺 lifecycle edge、缺 outcome metric、raw content 或敏感字段都必须 fail-closed。
