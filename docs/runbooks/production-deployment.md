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
