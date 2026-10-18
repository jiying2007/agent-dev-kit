# Managed native / Agent Value trust registry intake — 8.0.29

## Requirements
- Reject duplicate object keys and non-finite numbers at every registry JSON depth.
- Read only regular files through the existing strict JSON descriptor-based loader; reject manifest-directory and registry-leaf symlinks **before** `ensure_within` resolves them.
- Keep authority registries disabled/empty by default; source checks do not certify real native runtime or Asset Value effectiveness.
- Remain Python 3.8 compatible, preserve exact-SHA component release and Root promotion.

## Design
Use `agent_dev_kit.strict_json.read(path, max_bytes=limit, regular_only=True)` for native and Agent Value JSON registries. This uses one existing decoder, not another registry parser or a duplicate trust authority. The source preflights the `manifests` directory and registry leaf prior to path normalization.

## Verification
Exercise valid empty registry, nested duplicate-key and NaN payload rejection, byte overflow and leaf/parent symlink rejection under disposable temporary directories. Run the full multi-Python CI matrix and separately verify signed immutable component release. Real G21, G22, Product M5, LTA-04 and 90-day human Harness review stay externally pending.
