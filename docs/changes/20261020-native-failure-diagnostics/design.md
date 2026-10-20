# Design

## Failure-only control flow

Give existing workflow phases stable step IDs. After the unchanged successful candidate upload, add a collector guarded by `failure()` and successful trusted-source verification, Python setup and runtime installation. A failed authentication, input construction, prepare, run, finalize, signing, loader or candidate-upload phase can therefore be described without invoking any provider again. A second failure-aware condition uploads only after the collector itself succeeds. Neither step uses `continue-on-error` or changes the original exit code. Bootstrap failures before the helper's trusted prerequisites remain in normal job logs.

## Fixed input and output contract

Inspect only `plan.json`, `evidence.json`, `prepare-summary.json`, `run-summary.json`, `finalize-summary.json` and `production-loader.json` under the fixed campaign directory. Do not enumerate the directory. Each input is bounded to the existing 1 MiB JSON limit, read once through the strict regular-file reader, and hashed from those exact bytes. Ancestor and leaf symlinks, non-regular files, ambiguous JSON, excessive nesting and unknown fields are rejected. Existing v2 schemas validate plan and evidence; the three operation-summary shapes and loader summary have exact field allowlists.

Create an absent output directory with private permissions and exclusively write `diagnostics.json`, capped at 64 KiB. It contains fixed workflow outcomes, source/run identity, per-file presence or rejection codes, byte counts and digests, and validated numeric/hash/enum observation projections. Arbitrary strings, including schema-valid runtime names, versions, paths, error messages, environment text and failure reasons, are never copied. Only an explicit small vocabulary of known failure reason codes is retained; other details are withheld. Inputs produced by a phase that did not run are rejected as unexpected. Raw input files are never copied, including valid plan and evidence.

## Authority and privacy

The artifact is always `failed-campaign-diagnostics` with `lifecycle_authority=none-diagnostics-only`, `release_authorized=false` and both promotion flags false. Complete campaign observations can appear after a later signing or upload failure, but cannot change this overall diagnostic status. A workflow phase explicitly skipped is `not-run`; an attempted execution without an accepted observation, including a missing stage inside an otherwise valid partial evidence file, is `evidence-unavailable`. Existing explicit blocked-stage observations retain their blocked/semantic-not-run state. This diagnostic JSON is not a receipt or signature and is never fed into finalization or the trust registry.

The collector does not inspect private commands/assertions, raw stdout/stderr, auth helper/key, HOME settings, arbitrary runner files, receipts, signature bundles or registry candidates. An input validation error emits a fixed code rather than the validator's possibly sensitive exception text. Filesystem checks are defense in depth within the trusted hosted runner, not a replacement for runner isolation.

## Verification and budget

Use deterministic tests to cover semantic failure, earlier authentication failure, later signing failure, unavailable evidence, unstarted phases, excluded sibling files, free-text withholding, unknown top-level and nested fields, duplicate/non-finite/deep JSON, oversized input, symlink ancestors/leaves/output, non-regular files, fresh output ownership and CLI failure status. A workflow contract test ensures failure-aware collector/upload guards, fixed upload file, timeout and unchanged default-success qualification steps. Reuse the existing Native campaign regression rather than introducing a second campaign simulator or a provider call.

The implementation belongs in one typed module below the existing 30,000-byte cap, with one Python test file and the repository-standard shell wrapper. Existing CI list and mypy scope integration is coordinated by the main maintainer. No new job, dependency, artifact authority or schema migration is required.

Strict typing through the reused Native contract module exposed its existing mapping/dict return mismatch. The candidate builder now explicitly materializes `dict(contract.data)` before the existing deep copy. This makes its already-mutable candidate contract match the declared return type without modifying the source mapping, trust policy or receipt semantics; the existing 20-case Native regression covers the builder.

The existing hosted-hygiene test previously counted every `timeout-minutes` line as a job timeout, which cannot represent the two new step budgets. It now uses the already-declared PyYAML dependency to distinguish actual job and step mappings, reject duplicate keys, require every runner job's integer budget to remain 5–45 minutes, and require any declared step budget to be a positive integer no greater than its own job budget. Reusable calls remain delegates to their separately checked runner workflow. Missing/invalid/duplicate job budgets and invalid/duplicate/over-job step budgets have deterministic negative cases. The Native-specific test additionally checks both two-minute values at the actual step scope, so moving a value into an unrelated YAML mapping cannot satisfy the regression.
