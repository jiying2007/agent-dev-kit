# Production Deployment

Production deployment is target-explicit. ADK produces validated assets; the selected runtime adapter owns final installation, backup and rollback.

## Minimum Gate

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh openai-governance --summary-json
bash tests/run_all.sh --fail-fast
```

## Requirements

- deployment target is declared in `manifest.yaml:tool_targets`
- install or convert command has a rollback plan
- generated assets have a review owner
- runtime smoke evidence is recorded before production claims
