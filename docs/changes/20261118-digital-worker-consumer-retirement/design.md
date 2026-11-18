# 最小清理设计

- 根本目标是减少已不使用的消费者专属检查，而非引入统一兼容转发层。
- 删除 `manifests/integrations/digital-worker.json`、`.github/contracts/digital_worker_contract.py` 和 `.github/workflows/digital-worker-contract.yml`；原合同行为仍可从历史 SHA 审计。
- 保留 GitHub CI 的所有必需 Codex/Claude 检查；采用 11.4.9 源身份与版本唯一权威，不改历史 release、tag 和现行 signed artifacts。
- 若任何现役 workflow 或测试明确消费这 3 个文件，必须先修正真实依赖，不能通过跳过 required check 放行。
