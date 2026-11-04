# Source-byte Profile context ratchet — ADK 10.0.0

Date: 2026-11-04. Source identity: PR #236, branch commit `1819607e3fccc61de9041bde3c28af62a2c74819`; no native runtime, model or provider tokenizer was used. Asset files were counted from exact Git tree object sizes, and deferred support counted only `references/`, `scripts/`, `assets/` beneath selected Agent/Skill directories. The original `profile_context_footprint.py` source algorithm was preserved.

| Profile | Assets old → new | Entry bytes old → new | Full potential source old → new |
|---|---:|---:|---:|
| core | 27 → 27 | 129719 → 132309 | 170366 → 170421 |
| release-hardening | 23 → 23 | 106963 → 109553 | 145463 → 141635 |
| personal-core | 32 → 32 | 148797 → 151387 | 194509 → 190681 |
| embedded-fullstack | 54 → 54 | 232877 → 235467 | 292365 → 283982 |
| team-core | 37 → 35 | 166418 → 164575 | 230107 → 209030 |
| large-refactor | 55 → 55 | 235302 → 237892 | 299799 → 288438 |
| incident-response | 9 → 9 | 34519 → 36135 | 37820 → 39436 |
| research-intake | 20 → 20 | 83121 → 84916 | 121899 → 118623 |

## Reviewed rationale

- The prior source-growth ratchet was correct to fail: replacing rigid SOP instructions and language-only Skills changes the owned source body size. This is not a CI infrastructure failure and cannot be hidden by disabling enforcement.
- Shared profiles gained **2,590 entry bytes**, largely due to the risk-scoped commit/PR and requirements contracts and new Code Review guidance; their deferred supplemental reference sources decreased or remained nearly stable.
- `team-core` lost **two Skills**, lowering its total asset count **37 → 35**, entry bytes **166,418 → 164,575**, potential full source bytes **230,107 → 209,030**.
- `incident-response` does not inherit `core`: its focused shared gate grew **1,616 entry bytes** and support unchanged. Source bytes are not initial runtime context or real token consumption.
- All eight ratchet values now equal their **exact measured source usage** (no extra headroom). `fail_on_entry_file_growth` and `fail_on_potential_full_source_growth` stay `true`, and the existing negative test will still reject one additional byte of source growth.
- This is a scoped author-led source measurement/rationale. It does **not** create an independent reviewer identity, change release authorization, or satisfy native runtime/effect qualification.

## Reproduction and checks

- Repository `manifest.json`: resolve Agent/Skill Profile inheritance and unique assets.
- For each declared asset, count the exact SKILL.md or AGENTS.md Git blob size as entry bytes; recursively count only `references/scripts/assets` as deferred support.
- Run `bash tests/test_profile_context_footprint.sh` and complete Python 3.11/3.12 full regression on this exact new head; output source-byte measurement with version and SHA.
