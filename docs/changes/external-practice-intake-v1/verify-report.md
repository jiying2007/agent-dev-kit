# Verify Report：external-practice-intake-v1

## 状态

- ADK source：pass（strict、security、performance、full 54/54）。
- RC4 artifact/rehearsal：pass（双构建一致；RC3→RC4→rollback 恢复 39 项）。
- Root intake/reference contracts：定向 pass；root quick 53/53、full 58/58。
- Knowledge Hub：reviewing candidate 可精确检索，strict body coverage pass；未 active promotion/memory write。Hub 全局 199 条既有 frontmatter 漂移为外部存量边界。
- Review：blocker=0、major=0、minor=1（非阻塞维护建议）。
- Overall：`local-terminal-source-pass / review-passed / external-boundaries-explicit`。

## 不可扩大声明

- `degraded-empty` 的 Gitee live 结果只证明降级语义正确，不证明 Gitee 没有候选。
- fixture 与本地 rehearsal 不替代 remote CI、attestation、runtime campaign 或 field evidence。
- RC4 是 prerelease，不是 final `3.1.0` 或 Software M5 certified。
- mapped assets 已变化，但本 change 没有 source-to-live 写权限；不得声明 `~/codex`/`~/.codex` 已刷新。

## 外部后续门禁

1. owner 若授权 live refresh，按受控 source-to-live 链路刷新 `~/codex` 与 `~/.codex` 并记录回退证据。
2. remote CI/attestation、push/tag/publish 需独立授权；不得由本地 rehearsal 推断完成。
3. 双 runtime campaign、独立真实仓、第二位 operator、30 天 field evidence 和 reviewer approve 齐备后，才能评估 final `3.1.0` 与 Software M5 certification。
