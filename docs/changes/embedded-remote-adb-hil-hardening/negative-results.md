# Embedded Remote ADB/HIL Hardening Negative Results

## N1 下游旧命令不可用

- Before：`~/codex` 中调用旧 `scripts/devkit.sh match`，退出码 127，目标脚本不存在。
- Fix：`adk-runtime-router` 改用受信的 `~/codex/scripts/skill-search.sh` 和
  `tests.test_agent_routing_eval`。
- After：内容门禁确认旧入口无匹配；下游 routing eval 通过。

## N2 Skill 正文超过严格行数门禁

- Before：首次 `rtk bash scripts/devkit.sh validate --strict` 报告 skill 正文
  210 行，超过 140 行门禁。
- Fix：把远程 ADB/HIL 详细契约拆到
  `references/remote-adb-hil-contract.md`，SKILL 只保留路由、状态机和硬门禁。
- After：strict validation 通过；SKILL 正文 105 行。

## N3 下游出现重复版本与 sidecar/schema 不一致

- Before：首次 `check-skills.sh` 发现同名 skill 的 1.0.0/1.1.0 重复、旧
  `openai.yaml` schema 和新版本 sidecar 不完整。
- Fix：按 manifest 升级为 1.1.0，退役受管 1.0.0，统一 `interface:` schema
  并导入完整 sidecar。
- After：`check-skills.sh` 报告 `skills=63 errors=0 warnings=0`。

## N4 下游 registry 版本未同步

- Before：首次下游 `scripts/check.sh` 因 source registry 仍声明
  `adk-runtime-router` 1.0.0 而失败。
- Fix：将 `src/codex-home/skills/registry.csv` 同步为 1.1.0。
- After：下游全量 `scripts/check.sh` 通过。

## N5 Knowledge Hub 元数据和索引不完整

- Before：首次 `knowledge-check.sh --dry-run` 报告 source/validation 引用不一致，
  且 owner、review-date、status 三个索引缺少引用。
- Fix：补齐 runbook frontmatter、registry 和三个索引。
- After：Hub dry-run 检查 `status=pass`、`errors=[]`、`warnings=[]`。

以上均为设计与治理门禁的负路径证据；本变更未把真实设备失联、部署或 HIL
结果伪装成测试证据。
