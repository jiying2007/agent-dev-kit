# 负结果：intent-boundary-governance-v2

| 时间 | 阶段 | 命令/路径 | 结果 | 决策 |
|---|---|---|---|---|
| 2026-07-19 | planning | `rtk test -f .../proposal.md` | `rtk test` 被解析为 Bash 内建入口并输出 usage，exit 2，不能作为文件存在性检查 | 后续使用 `rtk bash -lc "test -f ..."`；不重试同一路径 |
| 2026-07-19 | source review | upstream `skills/in-progress/*` | `batch-grill-me`、`to-questionnaire`、`setup-ts-deep-modules` 尚未晋级稳定目录 | 保持 OBSERVE，不新增 ADK Skill |
| 2026-07-19 | architecture | upstream Claude plugin manifest | 平台私有 skills 数组与 Codex 当前单 root 示例不能证明可直接互换 | 拒绝复制/改名；仅吸收 invocation 方法 |
| 2026-07-19 | T1/T3 | `rtk bash scripts/check-official-docs-governance.sh --summary-json` | 首轮 fail=3：`adk-task-breakdown` 尚未同步 v2/work_item/permission markers | 保留失败并同步既有消费者；复跑 pass，未弱化 checker |
| 2026-07-19 | T1 residue | `tests/test_intent_boundary_governance.sh` | 首轮 residue gate 命中 manifest drift-control 中旧 schema 字面量 | 将 active contract 改为“retired schema”语义；历史 change provenance 保留，复跑 pass |
| 2026-07-19 | T5 version | `rtk bash tests/test_software_m5_ready.sh` | RC5 首轮在内嵌断言第 33 行失败；`release check` 明确报告 `.version-lock` 仍为 RC4 | 保留其他五个版本入口，通过单变量修正 `.version-lock`；release check 与 M5-ready 复跑 pass |
| 2026-07-19 | T6 patch | 首轮 `rtk apply_patch` | 52 个 metadata 已成功写入后，checker 正则上下文因反斜杠多转义匹配失败；apply_patch 并非整批原子事务 | 先以 legacy/true 计数确认 metadata 已完成，再只补 checker/tests/docs；不重复修改已成功文件 |
| 2026-07-19 | T6 plan inspect | `rtk jq '.operations[]' build/apply-plan.json` | plan schema 使用 `actions` 而非 `operations`，jq exit 5 | 改读 `.actions[]`，确认 53 个 overwrite 仅含 52 metadata 与 managed-files state；不影响 plan/apply |
| 2026-07-19 | T7 full | `rtk bash tests/run_all.sh --timing-json .../full-timing.json`（首次） | 55 项中 54 pass、1 fail；`test_no_external_repo_refs` 命中 tasks 中为 must_not_touch 列出的外部仓具体名称 | 泛化为“根仓既有无关已修改子仓与未跟踪目录”，保留边界语义且不携带外部仓引用；先定向复验，再重跑 full |
| 2026-07-19 | T7 review | strict prototype schema 对照 template/retention rule | 模板 verification/rollback/reference-check 字段会被 typed validator 当作 additional properties；空 evidence、伪 artifact marker、路径穿越和非 commit base 仍可能通过 | 判为 major 并修复 schema/validator/template/positive-negative tests；定向复验 pass，等待修复后 full |
| 2026-07-19 | T7 review | Codex checker 对照本机 OpenAI system Skill metadata | checker 只允许三种 interface 字段，会误拒绝官方已用 `icon_small`/`icon_large`，扩展性不完整 | 判为 major；保留 nested/policy 硬边界，同时接受并校验官方 optional interface fields，11 单测 pass |
