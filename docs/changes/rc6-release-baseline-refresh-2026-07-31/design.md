# 设计：RC6 release baseline refresh

## 版本与提交模型

1. 将产品版本从 `3.1.0-rc.5` 提升为 `3.1.0-rc.6`。
2. release source commit 包含版本、migration、campaign contract 和本变更的计划工件。
3. 从该不可变 commit 两次构建 artifact，并要求 tarball 字节一致。
4. 使用已验证 RC5 artifact 作为 previous，执行 `rc.5 -> rc.6 -> rollback`。
5. evidence commit 只增加 rehearsal、verification 和 review 工件，不再修改映射资产。
6. 根仓 gitlink 指向 evidence commit，`agent_dev_kit_release_commit` 指向 release source commit。

## 根仓 evidence 模型

- `software_m5_policy.release` 更新为 RC6、candidate SHA、RC6 rehearsal 和新 evidence report。
- `current-status` 将 source-to-live 标记为 `required-pending-owner-authorization`。
- release evidence 明确 `mapped_content_changed=true`，但 `dry_run/apply/post_apply` 均为未执行边界。
- scorecard、pilot ledger、task pack 和 M5 campaign contract 同步 RC6 身份，但不宣称 runtime campaign 或 field certification 已完成。

## 回滚与失败边界

- artifact 回滚：RC6 rehearsal 必须恢复 RC5 managed hashes。
- source 回滚：使用正常 `git revert`，不 reset 或重写历史。
- live runtime：本变更不执行写入，因此没有新增 live rollback anchor；后续授权 apply 时必须单独建立备份。
- 同版本 rehearsal、artifact 不可复现、checksum 漂移、full gate 失败均阻断收口。

## 验证矩阵

| 阶段 | 验证 |
|---|---|
| Version | manifest/YAML/pyproject/package/lock/README/docs/test 一致 |
| Source | strict、release check、security、Python 3.11/3.12 local-CI |
| Artifact | exact commit 双构建、`cmp`、checksum、source file count |
| Rehearsal | RC5 安装、RC6 升级、candidate rollback、RC5 hash restore |
| Root | policy/evidence/current-status/scorecard/ledger 一致 |
| Closure | `scripts/check-all.sh --full` 全通过 |
