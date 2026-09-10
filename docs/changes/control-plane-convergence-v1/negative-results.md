# Negative Results

- Broad repository-name grep over all documentation produced false positives for migration/removal/provenance text; active product surfaces are checked separately from historical evidence.
- Enforcing unique lifecycle/stage sort keys for workflows was invalid because multiple workflows may intentionally share a lifecycle stage.
- Treating every mention of `manifest.yaml` near SSOT language as legacy was too broad; the compatibility-mirror statement is valid and required.
- New shell tests without executable Git mode fail before test semantics execute; file mode is part of the product contract.
