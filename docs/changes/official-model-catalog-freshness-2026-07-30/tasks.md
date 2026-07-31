# 任务：official-model-catalog-freshness-2026-07-30

| Task | Status | Scope Write | Must Not Touch | Verify |
|---|---|---|---|---|
| T0 official-source-review | completed | 本 change 工件 | API/runtime/default model | OpenAI 官方 Models + Model guidance |
| T1 freshness-update | completed | official freshness record | source ID、其他 source | official docs governance |
| T2 supported-parity | completed | verify-report | host Python、全局依赖 | Python 3.11/3.12 full parity |
| T3 closeout | completed | state/negative/verify | commit/push/live apply | strict、定向、full evidence |

## Ownership 与执行边界

- owner：`agent-dev-kit`
- scope_read：official docs governance manifest、runbook、tests、官方公开文档。
- scope_write：本 change 工件和单一 freshness source record。
- must_not_touch：模型默认值、prompt、API 集成、凭证、用户运行目录和其他 dirty 变更。
- 本任务串行执行，不使用子代理。
