# Production Deployment

Production deployment is target-explicit. ADK produces validated assets; the selected runtime adapter owns final installation, backup and rollback.

## Minimum Gate

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh official-docs-governance --summary-json
bash scripts/devkit.sh security check --summary-json
bash scripts/devkit.sh release check --summary-json
bash tests/run_all.sh --fail-fast
```

## Requirements

- deployment target is declared in `manifest.json:tool_targets`, or is an explicit external handoff
- install uses plan/apply/receipt and has a verified rollback path
- release artifact includes checksum and SBOM
- generated assets have a review owner
- runtime smoke evidence is recorded before production claims
- hardware/field claims remain `field_not_verified` until real evidence exists

## Incomplete installation or rollback

An installation or rollback with a failed compensation is **not** a completed
rollback. Stop further plan/apply/rollback attempts against the affected target
and preserve `.adk-backups/<receipt-id>`, `.adk-staging/<receipt-id>`,
`.adk-rollback-staging/<receipt-id>`, and the active receipt. Never delete
these directories to make a retry pass. Make a byte-for-byte, permission-
preserving copy of the target before a supervised recovery; compare file
hashes to the preserved receipt/backup and restore missing assets explicitly.
A successful command exit or verified manual repair is required before
claiming the target is healthy. Atomic rename protection in one operation
does not imply power-loss-safe multi-file transactions.
