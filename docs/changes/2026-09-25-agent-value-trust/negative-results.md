# Required negative results

The managed verifier must reject:

- canonical/default contract because authority policy is disabled;
- missing or disabled registry authority;
- contract/registry backend mismatch;
- layer or runtime-target scope mismatch;
- unregistered receipt or canonical receipt digest drift;
- missing/unsafe/oversized signature bundle or bundle digest drift;
- missing/non-cosign verifier binary or verifier digest drift;
- missing certificate identity/OIDC issuer;
- verifier timeout or non-zero signature result;
- any receipt already rejected by the canonical Agent Value contract/receipt validators.

A valid synthetic runtime receipt may produce runtime-verified measurements, but v1 still requires production_authority=false, quality_evidence_eligible=false, owner_review_required=true and lifecycle_authority=none-evidence-only.
