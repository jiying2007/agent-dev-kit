# Negative results and falsification boundary

A global cache of public schema dictionaries was rejected: caller code could mutate a shared schema and poison future validation.

Caching explicit path schemas was rejected: a custom schema file may be modified between invocations. The regression mutates a custom Trace Summary schema and an external Run Evidence schema path; both reject an added absent field, while default checks continue to pass.

Disabling privacy/receipt validation, reducing bootstrap resampling, or dropping existing effect tests were rejected as invalid performance methods.

The first PR full regression exposed the unrelated, authentic 90-day Harness Owner review expiry (`last_verified_at=2026-07-18`, expired on 2026-10-17). Editing that timestamp automatically was rejected as fabricated human evidence. Instead, tests now require current `--gate` to remain partial/exit 2 when stale while report-only historical software fixtures remain deterministic. This preserves the true blocker.

Evidence is an isolated Python 3.13 local source-run timing A/B, not real Agent execution, token savings, or field certification.
