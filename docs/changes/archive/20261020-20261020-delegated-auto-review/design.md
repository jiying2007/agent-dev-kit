# Delegated review design

## Single authority and explicit opt-in

The new typed `agent_dev_kit.review_evidence.validate_review` validates evidence used by the existing workflow and Harness consumers. It does not create reviews. A repository-local `.adk/review-policy.json` records the owner's explicit delegation, authorized scopes and the exact authorization record. Other repositories retain their existing mode unless they opt in. AI identity and independence remain explicit; the responsible owner is not relabeled as the reviewer.

The frozen receipt contract is `adk-review-evidence/v1`: subject and scope, author identity, independent AI reviewer identity, actual reviewed/evidence-completed times, separate Spec/Quality verdicts, findings and limitations, policy/validator digests, and bounded original-byte source/evidence references. Source-change records additionally name exact original base/head commits and `original_patch_sha256`, binding a source reference to `evidence/original.patch` beside the record. The downstream frozen historical inventory independently checks all three original Git identities. Harness records cover exactly all seven dimension IDs. Allowed scopes also include delegated effect-value and longitudinal-summary review for downstream consumers; their real measurement and observation contracts remain separate.

## Content binding without a self-reference

Review outputs are not included in their own input digest. Exact referenced source files, policy and the validator are verified instead. Evidence references may be repository-relative or relative to the receipt directory, allowing the original archive operation to move an entire reviewed historical package without changing its original content. No broad source directory is excluded as a shortcut. Missing/changed content or altered review rules invalidates the review.

Reuse the existing strict JSON reader and regular-file protection, reject ancestor/leaf symlinks and noncanonical/traversing paths, enforce bounded reference count and byte totals, and compare digests from the same bytes read. Review must follow authorization and all claimed evidence completion times and must not be future-dated. Unresolved blocker/major findings cannot produce pass.

## Lifecycle and Harness integration

`review --review-evidence` validates the delegated record before any state mutation or report overwrite. An opted-in repository requires this record; ordinary CLI result/count values cannot grant delegated approval. The CLI owner is the actual lifecycle executor; the validated reviewer is recorded separately and need not perform source/state writes. Archive revalidates the same record before moving the package and writes its reviewer, dual-pass projection and exact receipt SHA alongside the distinct archive actor. It rejects an existing destination before state mutation. No force shortcut is used for this work.

Harness keeps raw scan outcomes authoritative. Metadata retains the owner and references the actual delegated review. Each verified date must agree with the validated review date; every dimension, including N/A, requires applicable review coverage. The output identifies the automated reviewer and repository-source scope, while field evidence stays not-verified. Existing stale/future/missing-structure tests remain.

## Validation, review and rollback

Derive negative cases from the acceptance criteria: date-only renewal, stale source/policy/validator, missing or duplicate dimensions, false reviewer independence, non-pass verdict, unresolved severe finding, temporal inversion, malformed JSON and unsafe files. Test existing lifecycle behavior plus receipt-before-mutation and archive revalidation. Run full existing regression and supported remote matrices. A separate AI reviewer reviews the entire implementation diff and the seven-dimension/source-change conclusions. Revert through a later protected versioned change if needed; preserve already-published versions and original historical evidence.
