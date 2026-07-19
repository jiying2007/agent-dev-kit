# Review Findings：intent-boundary-governance-v2

- Review Scope：manifest/schema、typed validators、direct-target adapter、task/planning/parallel/architecture consumers、Codex external handoff、迁移/版本、测试与 release 边界。
- Requirement Baseline：`proposal.md`、`design.md`、`tasks.md`、用户 ENHANCE/硬切授权。
- Verification Baseline：定向/strict/quick/security/benchmark 已通过；full 首轮 54/55，修复引用后及归档门禁修复后均为 55/55；Codex 最终 101 tests、五 profile 与零 drift 通过。
- Review Type：实现阶段结束后的独立视角 AI review；用户已授权方案与实施，但不把本报告表述为第三方人工审计或 Software M5 certification。

## Findings

| ID | Severity | File/Surface | Evidence | Required Action | Status |
|---|---|---|---|---|---|
| IBG-001 | major | `intent_boundary.py`、prototype contract/template | strict required-fields 与模板 verification/rollback/reference-check 不同构；空 evidence、模糊 artifact marker、路径穿越和非 commit base 未 fail closed | 同步 required fields，收紧 base/path/exit/reference rules，增加负例 | fixed；定向 pass |
| IBG-002 | major | `~/codex/tools/codex_assets/check_skills.py` | 本机 OpenAI system Skill 使用 `icon_small`/`icon_large`，原 checker 会作为 unknown interface fields 拒绝 | 接受官方 optional fields 并保持非空类型校验；不放宽顶层或 policy | fixed；11 单测与 63-skill check pass |
| IBG-003 | minor | review evidence | full 首轮唯一失败来自 change 文档携带外部仓具体名称 | 泛化 must_not_touch 描述并保留负结果 | fixed；定向与第二轮 full pass |
| IBG-004 | major | `check-change-governance.sh` / archive workflow | checker 强制 checklist 保持 `[ ]`，已完成工件无法合法 verify/archive；定制工件还缺模板等价章节 | checkbox 接受 `[ ]|[x]` 但标签精确匹配；补齐章节/Evidence Index；增加完成态正例和标签改名负例 | fixed；change gate、workflow、integration 与最终 full pass |

## False Positives / Accepted Historical Evidence

- RC4 名称仍出现在上一版 artifact、迁移源版本、版本比较测试和 changelog history；这些是回退/升级 provenance，不是活跃版本残留。
- task-package v1 仅允许出现在 negative fixture、拒绝消息和历史 change provenance；active Skill/Agent/manifest/template 无 v1 reader 或双写。

## Out-of-scope Suggestions

- 不执行 `$150` Codex/Claude 双 runtime M5 campaign；RC5 只声明 deterministic M5-ready，不声明 certification。
- 不新增上游同名 Skill/plugin/runtime，不恢复 submodule，不启用网络、hook、MCP 或外部写权限。

## Re-review Result

- blocker：0。
- major：0 open（IBG-001/002/004 均 fixed）。
- minor：0 open。
- Final release evidence：ADK commit `0fe2d4e` 双构建 SHA256=`6a82d1142b0b71568bce65acf814af68e82569d7679f9edc8abd96ca8be3c783`；RC4→RC5 hard-cut rehearsal pass；Codex source commit=`684f7f8`。
- Pending gate：仅受管 workflow 状态迁移、归档移动与 root gitlink/status commit；无技术 blocker/major。
- Final Verdict：`pass`，限本地 RC5 release candidate 与运行资产闭环；不等同 remote release 或 Software M5 certification。
