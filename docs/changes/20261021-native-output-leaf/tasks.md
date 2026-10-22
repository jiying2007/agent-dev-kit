# Tasks

- [x] TASK-001: Add real CLI regression for existing/dangling external leaves on both prepare outputs. VERIFY: 3 selected methods on original source returned exit 1 with 6 subcase failures; the regular-output control passed. Original stdout/stderr and terminal receipt are retained in `oct21-continue-native-implementation/red-tests/`.
- [x] TASK-002: Guard the lexical output leaf before resolution and preflight run output before execution. VERIFY: all 23 native campaign tests pass, including actual prepare CLI no-clobber cases, the run execution spy and normal external outputs. The independent original reproduction is also rerun against the fix; its terminal evidence is retained separately.
- [ ] TASK-003: Independently review exact source and tests, run required supported regression, and synchronize the component patch version. VERIFY: source digests, terminal command receipts, Spec/Quality conclusions and clean diff.
- [ ] TASK-004: Complete protected PR, fresh-main CI, immutable component release and Root exact promotion. VERIFY: canonical remote identities, original release asset hashes/signature and downstream checks. Remote completion is recorded only after observation.

Lessons lookup before Build: `knowledge/L2-domain/lessons.md` is absent at the pinned baseline. No matching historical lesson is asserted.

Component version identity is synchronized to 8.0.38 and `versioning verify-identity` passes. TASK-003 remains open until independent review and supported regression complete; TASK-004 remains open until remote delivery is actually observed.

## 2026-10-22 local candidate checkpoint

Independent Native Spec and Quality reviews pass against the exact source/test bytes. The focused Native suite passes 23/23. A fresh Harness source review binds the current candidate, with six applicable dimensions passing and one not applicable; field evidence remains not verified. Four official source records that expired on 2026-10-21 were actually re-reviewed under the separate `20261022-official-reference-review` contract.

The resulting candidate passed all 101 full regression scripts on Python 3.12.14, exit 0, at 2026-10-22T00:33:47Z. Before/after tracked-source state digest is `6ef6193e5af9457be4a31dd7274cd3c1da409c256cc0a75699e845afa539b443`. This checkpoint was added after the run with executable source unchanged. Other supported Python versions and the protected remote matrix are not verified here, so TASK-003 is only partially complete. TASK-004 remains open: no remote candidate commit, PR, immutable 8.0.38 release or downstream promotion has been observed.
