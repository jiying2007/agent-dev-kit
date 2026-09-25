# Native target conformance candidate campaign

This command closes the **evidence collection** side of native target conformance without claiming certification.

```bash
bash scripts/devkit.sh target native-campaign \
  --target claude-code \
  --profile core \
  --runtime-binary "$(command -v claude)" \
  --runtime-name claude \
  --runtime-version 2.1.138 \
  --commands /absolute/native-stage-commands.json \
  --authority-id owner-reviewed-native-candidate \
  --execution-authority human-approved \
  --verification-backend external-signature-verifier \
  --output /absolute/native-receipt.json \
  --summary-json
```

The commands file is data, not a shell script:

```json
{
  "schema": "adk-native-target-campaign-commands/v1",
  "stages": {
    "discovery": ["/absolute/runtime-or-reviewed-wrapper", "..."],
    "load": ["/absolute/runtime-or-reviewed-wrapper", "..."],
    "trigger": ["/absolute/runtime-or-reviewed-wrapper", "..."]
  }
}
```

All three command arrays must be different. The campaign exports the selected Skill bundle to an isolated temporary target root and exposes that path through `ADK_TARGET_ROOT` plus the current `ADK_TARGET_SMOKE_STAGE`. The stage command is responsible for invoking the native runtime with reviewed permission, persistence, settings-source and provider/auth flags.

The collector records command/result digests, exact runtime binary digest/version pin, deterministic bundle digest, prospective normalized target-contract digest, timestamps, bounded stdout/stderr byte counts and authority metadata. Raw stdout/stderr are hashed and discarded. A timeout, non-zero exit, output flood, repeated stage command/result evidence, unsafe command file, missing runtime or existing receipt path fails closed.

## Authority boundary

A successful campaign emits a schema-valid `adk-native-target-conformance-receipt/v1`, but its result is always:

- `trust_verification=not-run`
- `certification=not-certified`
- `promotion_eligible=false`
- `lifecycle_authority=none-evidence-only`
- `release_authorized=false`

The receipt's stage authority hash proves deterministic structure only. It does **not** prove who executed the runtime or that a CI/human authority is trusted. The existing target contract therefore remains static until a separately managed external-signature or CI-provenance verifier validates the receipt and the reviewed runtime contract is promoted.

## Isolation and privacy

ADK itself writes only to an isolated temporary bundle and the explicit receipt output path. It does not write live `~/.claude` or `~/.config/opencode`. Stage commands inherit the caller environment so an authenticated runtime can be used; therefore command design must explicitly disable unwanted user settings, tools, persistence and network integrations as required by the target.

For Claude Code, official documentation supports project/global skills and `CLAUDE_CONFIG_DIR`; OAuth/application state is separate from the config directory. For OpenCode, native skills are discovered from project/global sources and full Skill bodies/support files are loaded on demand. Those runtime facts inform the command plan but are not copied into ADK core semantics.

## Recovery

A failed campaign does not write a receipt. Fix the failed stage or runtime/auth boundary and re-run into a new output path. Never edit a candidate receipt by hand to make it pass; later trust verification must bind the exact receipt digest.
