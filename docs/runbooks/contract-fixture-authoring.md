# Contract Fixture Authoring

This runbook defines how ADK turns external harness, loop, eval or workflow practices into local contract fixtures.

## Scope

Use this workflow when a reference source provides a useful engineering pattern, but ADK should absorb only the contract shape, evidence fields, fixture pattern or gate behavior.

Do not use this workflow to import upstream runtime code, benchmark data, containers, hosted services, daemons, hooks, MCP servers, GUI automation, secrets or credentials.

## Authoring Flow

1. Map the source to an existing ADK contract, or create a new contract only when reuse is not sufficient.
2. Fill `templates/governance/contract-fixture.md`.
3. Create a clean-room positive fixture with `runtime_enabled=false` and `fixture_mode=method-only`.
4. Create at least one negative fixture that is rejected by the gate for a precise `expected_failure`.
5. Add the fixture paths to the owning manifest.
6. Extend the owning checker so it validates the positive fixture and proves the negative fixture fails for the expected reason.
7. Record evidence in the adoption matrix or implementation report.

## Required Positive Evidence

| Field | Purpose |
|---|---|
| `source_mapping` | Links the fixture back to reviewed reports and source ids. |
| `contract_under_test` | States which ADK contract the fixture proves. |
| `oracle_or_assertion` | Makes the pass condition deterministic. |
| `verification_command` | Gives the local command that checks the fixture. |
| `evidence_path` | Points to the tracked fixture or report evidence. |
| `rollback_path` | Explains how to remove the fixture and manifest reference. |

Pipeline fixtures must also include local CI parity. Artifact lineage fixtures must include `version_or_digest`, materialization time and retention policy.

## Required Negative Evidence

Each negative fixture must include:

- `expected_failure`
- `contract_under_test`
- `missing_or_invalid_field`
- `verification_command`

The checker must reject the negative fixture and confirm the observed failure contains the declared `expected_failure`. A negative fixture that passes is a gate failure.

## Promotion Boundary

Contract fixtures are method-only by default. Runtime enablement requires a separate owner-approved gate with supply-chain review, permission boundary, dry-run behavior, rollback path and live evidence.

## Harness Loop Example

The harness/loop engineering gate demonstrates this pattern:

- Positive fixture: `fixtures/harness-loop-engineering/pass/local-fixture-bundle.json`
- Negative fixtures: `fixtures/harness-loop-engineering/fail/*.json`
- Manifest: `manifests/harness_loop_engineering_contracts.json`
- Checker: `scripts/check-harness-loop-engineering-contracts.sh`
