# Profile context footprint

Use the source-layer footprint command before changing profile composition:

```bash
adk profile-footprint --profile core --summary-json
adk profile-footprint --profile core --compare embedded-fullstack --summary-json
```

The command measures exact UTF-8 source bytes for resolved `AGENTS.md` and `SKILL.md` entry surfaces, and separately totals deferred `references/`, `scripts/`, and `assets/` files. The byte ledger is deterministic. The reported token estimate is only `ceil(bytes/4)`; it is not a provider tokenizer measurement and must not be used as a billing or context-window fact.

Use `entry_context.bytes` when deciding whether a profile's always-visible source surface is growing. Treat `deferred_support.bytes` as a potential on-demand surface rather than assumed initial context. Compare profiles with `--compare` to see marginal asset and byte growth; byte reduction is not itself proof of task-quality improvement.

For direct targets, use the isolated source-layout probe:

```bash
adk target-source-probe --target claude-code --profile core --summary-json
adk target-source-probe --target opencode --profile embedded-fullstack --summary-json
```

This writes a temporary export, re-discovers the exported inventory, verifies every file digest, and loads text entry files as UTF-8. A PASS proves source-layout discovery/load only. It does not launch the native runtime, does not touch a user live directory, and emits `native_runtime_evidence=false`, `certification=not-certified`, and no lifecycle authority.

Native discovery/load/trigger still requires the existing target/runtime evidence path. Real token usage still comes from runtime Run Evidence when available. Keep those evidence levels separate.
