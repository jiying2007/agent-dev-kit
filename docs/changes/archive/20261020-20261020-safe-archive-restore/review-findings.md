# Independent safe archive restore findings

Actual reviewer: `ai/root/external_methods` (`/root/external_methods`). Implementer and lifecycle actor: `ai/root`. The reviewer remains independent from source and lifecycle mutation.

## Exact source

- Original base: `a17e7e61a01845cc1b1165c9f9137b689bb2e1de`.
- Frozen candidate: `56b8aaffb5395a8fb080bf298857ed8573c06380`.
- Complete original patch: `evidence/original.patch`, SHA-256 `8b56e9f4340f2cb8d26239c87f2eef47cffba89cc1df9b121f3ccebde0954b97`.
- Final distinct verdicts for the repaired source: Spec `pass`; Quality `pass`.
- The independent complete-patch and material confirmation time is recorded in `review-evidence.json` after that confirmation actually occurs.

## Retained finding and verified repair

`HARNESS-RECOVERY-001` was an actual major in the original baseline: the public legacy restore path removed the target before validating the archive and accepted a top-level name unrelated to the requested target. The prior baseline verdict was `needs-fix`; it is not replaced with a retroactive pass.

The reviewed repair makes the existing public shell command a thin adapter to the typed transaction core. It locks the target, rejects unsafe ancestry and incomplete prior staging, fully consumes gzip checksums, bounds compressed and expanded content, and validates every archive member before mutation. Only canonical, unique regular files/directories under the exact target name are accepted. Links, traversal, special entries, duplicate paths and incompatible layouts fail closed.

Extraction uses private staging. Target replacement occurs only after successful validation and extraction. Failed commits attempt compensation; failed extraction, commit or compensation retains bounded diagnostic staging and prevents a blind retry from overwriting it. Existing target contents remain available or are restored according to the actual failure phase. Successful cleanup is distinguished from a cleanup failure after a completed restore.

Eight actual temporary-filesystem tests cover valid public roundtrip, CRC damage, wrong top-level identity, traversal, links/special/duplicate entries, symlink paths, extraction failure, commit failure and compensation failure. The independently reviewed source SHA values were verified after environment recovery. Fresh actual output is retained in `.adk/reviews/source-validation-20261020.txt`.

## Closure and limits

The major is `fixed` on this exact source; no blocker or major remains open. This is an actual source and filesystem recovery review. It does not assert a live production restore, runtime qualification, field observation, paid inference, human review or Product M5 release authorization. Remote delivery still requires the protected component release workflow and exact Root promotion.
