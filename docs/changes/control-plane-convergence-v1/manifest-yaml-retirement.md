# Manifest YAML 兼容层退役

- status: implemented-pending-fresh-ci
- decision: 删除 `manifest.yaml`；`manifest.json` 是唯一结构化 Manifest SSOT。
- scope: 仅退役 Manifest YAML 镜像；workflow、target 等独立 YAML 合同继续按各自 schema 使用 PyYAML。
- shell migration: `scripts/lib-manifest.sh` 保留稳定函数接口，但全部结构化读取改由 `agent_dev_kit.manifest_query` 查询 canonical JSON。
- temporary tombstone: `tools/check_manifest_sync.py` 暂时仅为 `release.py` 的旧调用入口保留，语义改为禁止 `manifest.yaml` 重现；下一批迁移 release 后删除该入口。
- rollback: 如果发现真实、受支持的下游仍直接依赖 `manifest.yaml`，回退整个原子退役提交并明确登记 consumer；不得静默重新生成第二 Manifest SSOT。
- required evidence: Manifest contract v3、consumer boundary、Python 3.11/3.12 full regression、release check 与 deterministic package evidence。
