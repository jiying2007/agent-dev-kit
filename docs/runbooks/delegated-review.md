# Delegated automatic review

The owner may explicitly delegate source and evidence review to an independent AI reviewer. This repository's delegation is recorded in `.adk/review-policy.json`; its authorization file preserves the actual user instruction. Other repositories do not inherit this opt-in from merely installing ADK.

## Existing lifecycle

For an opted-in repository, the existing `review` operation requires the change's canonical `review-evidence.json`. The validator binds the policy, declared independent reviewer, separate Spec and Quality verdicts, findings, times and original source/evidence bytes before a positive state transition. `archive` revalidates the same record. The lifecycle actor is the person or agent actually executing that transition; the validated reviewer is recorded separately and can remain read-only. The owner remains the responsible delegator.

```bash
rtk scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --owner <actual-lifecycle-actor> --review-evidence <change-dir>/review-evidence.json
rtk scripts/devkit.sh archive --change <change-id> --owner <actual-lifecycle-actor>
```

Keep full semantic reasoning in `review-findings.md` before the lifecycle creates its summary `review-report.md`. Source-change records bind their exact base/head and `original_patch_sha256` to the source reference `evidence/original.patch`; the historical consumer independently checks its known original Git identities. Relative-to-record evidence references remain valid after the canonical archive move. Preserve historical verification files and dates; append the actual present review rather than rewriting past facts. The approval validator does not itself generate pass findings or infer them from CI. Its identity fields document the review process; they are not platform authentication.

## Harness source review

Every dimension references an actual review record covering exactly the seven known dimensions. Keep the responsible `owner`; record the AI reviewer separately. Only a valid source-bound review can supply the actual new `last_verified_at` date. Existing structural failures, stale/future dates, missing references, N/A applicability and scan errors retain their effect. `field_evidence_status=not-verified` remains independent of repository-source review.

## Review evidence and limits

The sole validator is `agent_dev_kit.review_evidence.validate_review`. Inputs use `adk-review-policy/v1` and `adk-review-evidence/v1`. Records bind source/evidence files, policy bytes and validator bytes; they do not hash themselves into their own inputs. Independent AI identity must differ from author identity. A review must follow authorization and evidence completion, have both Spec/Quality pass and no unresolved blocker/major, and keep explicit limitations. Canonical paths, regular files, strict JSON and bounded reads are required.

Root can call this same API with its own evidence root and the exact pinned ADK as `policy_root`; it does not create a second approval authority. Delegated G22 or longitudinal review only reviews genuine existing observations and cannot supply absent signatures, trials or field events. Protected CI, immutable release and exact-source promotion remain separate mandatory delivery evidence.
