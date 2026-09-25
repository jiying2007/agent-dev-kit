# Native target campaign

This runbook turns native target verification into a reproducible, privacy-safe pipeline without promoting the active target contract.

## 1. Prepare

Create an external commands JSON with exactly four command arrays: `version`, `discovery`, `load`, and `trigger`. Every command must start with the same absolute runtime binary path; wrappers and PATH-only executable names are rejected. Commands are hashed into the plan but their raw arguments are not copied into repository evidence.

```bash
bash scripts/devkit.sh native-campaign prepare \
  --target claude-code \
  --profile core \
  --runtime-binary /absolute/path/to/claude \
  --runtime-version 2.1.138 \
  --authority-id ci-native-conformance \
  --execution-authority ci-approved \
  --verification-backend ci-provenance-verifier \
  --auth-mode home \
  --commands-json /absolute/private/commands.json \
  --receipt-path reports/runtime/claude-native.json \
  --plan-out /tmp/native-plan.json \
  --candidate-contract-out /tmp/claude-runtime-candidate.json \
  --summary-json
```

Prepare binds the current static target contract, exact ADK source version, skills-only rendered bundle digest, runtime binary digest/version, trust backend, authority, receipt path and four command digests. It also creates a future runtime target-contract candidate whose normalized contract digest is stable before evidence is added.

The candidate is not an active contract. Do not copy it into `manifests/target-contracts/` yet. Campaign CLI outputs that resolve inside the repository are restricted to `reports/runtime/`; plan/candidate/final-contract files should normally stay in an external temporary directory until owner review.

## 2. Run

```bash
bash scripts/devkit.sh native-campaign run \
  --plan /tmp/native-plan.json \
  --candidate-contract /tmp/claude-runtime-candidate.json \
  --commands-json /absolute/private/commands.json \
  --runtime-binary /absolute/path/to/claude \
  --evidence-out /tmp/native-evidence.json \
  --summary-json
```

The runner first executes the explicit runtime version probe and requires the planned version string. It then creates one isolated project root, places the rendered bundle under the reviewed native project configuration directory (`.claude/` for Claude Code, `.opencode/` for OpenCode), and runs independent discovery/load/trigger commands with the project root as cwd. The relative `skills/...` layout from the target contract is therefore evaluated through the runtime's real project-level discovery surface.

Default `--auth-mode none` omits HOME. `--auth-mode home` exposes only HOME/XDG cache plus certificate paths; provider tokens and the parent process environment are not inherited automatically. HOME is preserved separately from the temporary project config root, so project-local skills can be tested without replacing Claude's user config/credential directory. Each stage also receives `ADK_TARGET_PROJECT_ROOT` and `ADK_TARGET_ROOT`; the latter points to the reviewed project config directory.

Raw stdout/stderr and raw commands are never written to evidence. Evidence records byte counts, SHA-256 digests, start/end time, duration, result digest and a non-secret environment projection. Output is bounded and execution is time-limited.

Any stage failure blocks subsequent stages. A failed or blocked campaign returns non-zero and cannot be finalized.

## 3. Finalize

Only a complete three-stage campaign can produce a native conformance receipt:

```bash
bash scripts/devkit.sh native-campaign finalize \
  --plan /tmp/native-plan.json \
  --candidate-contract /tmp/claude-runtime-candidate.json \
  --evidence /tmp/native-evidence.json \
  --receipt-out reports/runtime/claude-native.json \
  --final-contract-out /tmp/claude-runtime-final.json \
  --summary-json
```

Finalize creates an `adk-native-target-conformance-receipt/v1` and fills the future target contract with receipt identity, digest and verified timestamp. It refuses to overwrite the active target contract.

The result is only `ready-for-signature-and-registry`. It is not certified and has no release authority.

## 4. Signature, registry, promotion

After finalize:

1. Sign/attest the exact receipt with the reviewed external/CI provenance authority.
2. Add the receipt canonical digest, Sigstore bundle digest/path, target scope, certificate identity/issuer and digest-pinned cosign binary to the managed trust registry.
3. Verify the future contract using the production loader.
4. Review and separately promote the target contract from static to runtime.

Skipping any step is forbidden. Source-layout probes, campaign fixtures or unsigned receipts cannot replace native certification.


## Project layout authority

`manifests/native_campaign_target_layouts.json` is the reviewed source for native campaign project configuration roots. It is freshness-bounded and must cover every direct target. The current mappings are:

- `claude-code -> .claude`, backed by the Claude Code Skills documentation.
- `opencode -> .opencode`, backed by the OpenCode Skills and configuration documentation.

This manifest is execution-layout metadata, not a new target contract wire format. Changing it requires source-version review and regression; campaign plan/evidence/receipt v1 schemas remain unchanged.


### Authentication and global-skill caveat

`auth_mode=home` intentionally preserves the user's normal HOME so an authenticated runtime can start. That can also make user-global runtime configuration/skills visible. Project-local placement therefore proves that the campaign bundle is on the native project discovery surface, but does not by itself prove that no global source can shadow or influence a skill. A real certification campaign must use a uniquely identifiable canary/skill identity or equivalent native evidence and must record any global-source collision risk; a project-layout PASS alone is insufficient for native certification.
