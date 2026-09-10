# Manifest YAML 兼容层退役

- status: implemented
- decision: 删除 `manifest.yaml`；`manifest.json` 是唯一结构化 Manifest SSOT。
- scope: 仅退役 Manifest YAML 镜像；workflow、target 等独立 YAML 合同继续按各自 schema 使用 PyYAML。
- shell migration: `scripts/lib-manifest.sh` 保留稳定函数接口，但全部结构化读取改由 `agent_dev_kit.manifest_query` 查询 canonical JSON。
- release migration: `src/agent_dev_kit/release.py` 已删除 Manifest YAML source-distribution 条目与 JSON/YAML mirror subprocess；发布身份只绑定 canonical `manifest.json`。
- tombstone removal: `tools/check_manifest_sync.py` 与一次性 v2→v3 migration 工具均已删除，不再保留历史兼容执行入口。
- regression naming: 当前产品成熟度合同使用 `tests/test_product_maturity_v5.sh`；旧 v4 文件名已退役。
- rollback: 如果发现真实、受支持的下游仍直接依赖 `manifest.yaml`，必须通过显式兼容提案重新评审；不得静默重新生成第二 Manifest SSOT。
- required evidence: Manifest contract v3、consumer boundary、Python 3.11/3.12 full regression、release check 与 deterministic package evidence。
