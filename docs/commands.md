# Commands

`agent-dev-kit` exposes generic ADK asset commands. Runtime-specific adapters are optional targets; the core package does not ship platform-specific handoff paths.

## install

Install agents and skills into a supported local tool directory.

```bash
bash scripts/devkit.sh install --tool claude-code --profile core --mode copy --target /tmp/adk-target
```

Supported tools are declared in `manifest.yaml:tool_targets`.

## convert

Convert ADK assets to a supported target format.

```bash
bash scripts/devkit.sh convert --target claude-code --profile core --out dist --clean
bash scripts/devkit.sh convert --target opencode --profile core --with-optional-skill adk-test-flakiness-triage --out dist --clean
```

## runtime-boundary

Verify that the active runtime surface remains generic and does not expose a platform-bound handoff path.

```bash
bash scripts/devkit.sh runtime-boundary
```

## openai-governance

Validate official OpenAI Developers reference freshness and promoted ADK contracts.

```bash
bash scripts/devkit.sh openai-governance --summary-json
```

## validate and test

```bash
bash scripts/devkit.sh validate --strict
bash tests/run_all.sh --fail-fast
```
