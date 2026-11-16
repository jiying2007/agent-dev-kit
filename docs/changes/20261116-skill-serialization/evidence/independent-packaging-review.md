# Independent evidence packaging review — v11.3.11

**PASS.** Completed `2026-11-16T12:49:36.245150+00:00` by `ai/root/delivery_review`. Open blocker/major/minor: **0/0/0**.

This verdict covers the nine additive evidence files listed below. It preserves the earlier Spec/Quality source verdict and does not certify release completion.

## Reviewed identities

| Role | Exact identity |
|---|---|
| Baseline | `b20df018ca62436dd026daed6ec6944d4a45cbbd` |
| Actually tested local source | `5b253b8885447f35f015d63950db025b2d82b2ba` |
| Canonical remote source | `a94ae0d551a8ede9f8387e4cd03eb41daf1894b1` |
| Identical full source tree | `35fa327dff1c4339c5637a427be64ca6c810f705` |
| Original canonical patch SHA256 | `446fcc6a3a599051177bfd00a5fd5590b3d270fbad41554d5dfc9752eba605e7` |
| Original independent source review time | `2026-11-16T12:40:08.744429+00:00` |
| Typed record SHA256 | `d6690b875f2796099b8d43d1c906eb26c39cef7f388ae9a66d292806b0248ead` |

The local and canonical source commits have different metadata. Their tree and all 28 frozen changed files match exactly. Local full regression results belong to the local commit; they were not relabeled as a run on the remote commit.

## Completed checks

- All 28 frozen source files match canonical source in both working tree and index; full-index binary patch and source bindings are valid.
- Both retained independent source-review files exactly match the original scratch reports, including the original review time, findings and limitations.
- All 14 bundle items strictly decode and match their declared raw byte lengths, SHA256 and original files. Decoding used a 16 MiB ceiling per item. The first 13 serialized records reconstruct the original bundle SHA256 `050ae015582cd6a29e863e825094d9fc34836df42c1c3be0bb3d951878bac885`.
- Production `validate_review` passes with 29 source references and 5 evidence references, without changing policy, validator, clock or original source verdict.
- `verification.md` explicitly corrects historical exit 2 to actual raw exit 1, keeps the frozen history, and distinguishes source, local execution, packaging and release.
- Post-stage format/security commands are real exit 0/no-timeout runs against this exact nine-addition staged diff. Format retains existing non-executable-script warnings; security reports 2,615 scanned files, no warnings and no failures. Neither gate was rerun by this reviewer.

**Snapshot limitation retained:** security `before.indexed_tree` failed with exit 128 because `index.lock` existed; its after tree is valid. Format has complete equal before/after snapshots. Both receipts retain equal HEAD/status/staged-diff snapshots matching the present staged bytes. The first report-builder assertion exposed this limitation and failed; the corrected report preserves it. Security alone is not described as having a complete successful before/after tree snapshot.

The earlier full run remains 102/102, exit 0, no timeout, 342.106898 seconds, with both actual log streams retained. The eight original profile budgets remain unchanged. Packaging does not require another full regression when these frozen sources and raw results remain identical.

## Findings and resolutions

**SER-PACKAGING-01 — minor, fixed.** The draft bundle omitted the already executed six-mutant probe runner. The parent appended its exact original 7,159 bytes as item 14 (SHA256 `f6efe6f8de6852ebc0dae68d7a37f6ae5340d088cc78e159261d3f2b02d785f7`). All original 13 records remain unchanged. Bundle, summary and typed evidence hashes were refreshed and production validation passed. No tests or sources were changed.

**SER-REVIEW-01 — minor, closed by visible append-only erratum.** The unsupported `--profile` command actually exited 1. The first section of `verification.md` corrects the frozen prose that said 2; it does not rewrite the original failed-command receipt or the source history.

## Exact reviewed packaging files

| Path relative to change directory | Bytes | SHA256 |
|---|---:|---|
| `review-evidence.json` | 9498 | `d6690b875f2796099b8d43d1c906eb26c39cef7f388ae9a66d292806b0248ead` |
| `verification.md` | 4752 | `64c384c7ac7d4abb0074f16d36ceda3e0ad988596c87a1aa96cc50128fb3c80b` |
| `evidence/source-bindings.json` | 7474 | `df6b73b457ede661d74a342b39340be60548eafcb78ed80a3149a165e6dc5e04` |
| `evidence/original.patch` | 144014 | `446fcc6a3a599051177bfd00a5fd5590b3d270fbad41554d5dfc9752eba605e7` |
| `evidence/execution-bundle.json` | 61324 | `851f5891f4044649dcc11ff1e0a8fec08a13a0e03cd3c2b06b3c9c432a1bade4` |
| `evidence/execution-summary.json` | 1793 | `0b4c7789c060ab448536c3c893e05946fa88f74da874d61f20e2e8de4e84d36c` |
| `evidence/review-validation.json` | 497 | `67d59d95ae963ba98692ef498d07a93b92be7a208c1c127473699a4ac6b4a2fb` |
| `evidence/independent-source-review.json` | 26917 | `901ba57d1a79dbe3514ed41ccf4551214af3bfd602e4c97515ef0a4f9ccf4909` |
| `evidence/independent-source-review.md` | 6301 | `59448db4d0a9bdeb6c33ad6ce0d1b9361d5b0ba8aad7ebde7b7eeadd83bc07f2` |

## Raw bundle members

| Name | Raw bytes | SHA256 |
|---|---:|---|
| `full-regression/started.json` | 754 | `c59ab6824581b42ec71468d4195b401286f3d1e850f45da3385d182bdcb58b63` |
| `full-regression/receipt.json` | 1613 | `784190caf19a87688e9c296a5f629deebe384f77337069388ddc4d9de589af0a` |
| `full-regression/timing.json` | 8224 | `9c67ac846bd18ecf4fcfa3fabdca6f85a06461bf46fbb71d0a2646b092ace36d` |
| `full-regression/stdout.log` | 34242 | `621c0bd6048df285caeb1bc93549ecb2e8ecc2b334caa2669ea9ab9ebcb17bdb` |
| `full-regression/stderr.log` | 59337 | `8271d289edb49714864b71029b3d2917628c517b1bb4b59f1ab51b57d43ea518` |
| `profile-checks.json` | 13100 | `6f776cb3d5a6a99297a81ef52033aff9c2331e4e0a1d6a214c33206890d7bbe8` |
| `check_profiles.py` | 2602 | `edf0c9dd9a35b91890a3df0ee07c536621aec6e7c1168b4cb2e0f785599eac11` |
| `consumer-review.json` | 20904 | `601466feed3a8345351871bc9ff8dcccf70266d92ce9705177026de49109bbca` |
| `independent-probe.json` | 46412 | `a60f8ac8f3ed68789485ecc72ef9cd1469732317e07f1a1cb59ac1285f48efd2` |
| `consumer-fixture/README.md` | 673 | `270bc27637504f6fccfec4bc43d67089accef6d1436e94a186509364bf00d9f0` |
| `consumer-fixture/models.py` | 203 | `2d4d9f78848b114ec487595136075a12336c500872826e99728a1322df781797` |
| `consumer-fixture/diagnostics.py` | 261 | `80eacc91d3eb04c29902b8e21c0bf1de0625fff504ac534c3933508354aca32e` |
| `run_command_receipt.py` | 2718 | `ca62aaa075d5a60c87b66af987543d2b14f9813f0228684b7a1379a7b6c5ecfe` |
| `reviewer-serialization-probe.py` | 7159 | `f6efe6f8de6852ebc0dae68d7a37f6ae5340d088cc78e159261d3f2b02d785f7` |

## Release and delivery boundary

Read-only GitHub job evidence confirms release run **43867568341**, bounded retry package job **133303201333**, failed at **Validate and smoke**. **Publish GitHub Release was skipped.** The current verification text reports this failure and leaves the cause unresolved. Local success on a different toolchain does not establish the CI root cause, and Ninja `[1/4]` identifies completed build edges rather than a first-compiler hang.

Exact remote v11.3.11 PR/main evidence, successful immutable release evidence and Root source-only promotion receipts remain separate delivery requirements. This packaging PASS must not be reported as completion of those steps.

## Review scope and limits

Read all nine packaging files and mechanically matched the 28 frozen source paths; decoded and checked every bundle item; inspected the original probe runner, consumer task/fixture/report, full-run identities, current typed bindings, post-stage gate receipts, and observed release jobs. The earlier independent source report supplies the semantic source assessment. This packaging pass did not repeat the full source review or full 102-entry suite.

The consumer remains a single fresh-context observation with no retained complete execution transcript. It does not establish paired/model A/B effects, cost or latency improvements, native-runtime qualification, or an actual ADK credential incident. The 14-item bundle is lossless for its listed members, not a complete transcript of all tool interactions.

No repository source, index/ref or remote state was changed by this reviewer; only scratch review artifacts were written. Parent staging is recorded separately. Initial/final check results and the checker source are embedded in the JSON report, together with gate log text and the observed GitHub jobs result, so the report is independently inspectable without unspecified check files.

The JSON/Markdown reports are intentionally excluded from their own reviewed nine-file manifest. Parent may append byte-exact copies and run integrity checks. This is not a circular self-hash or a pre-approval of future source changes.

JSON report: `independent-packaging-review.json`, 54315 bytes, SHA256 `0ea853162c7e891f05390011c32b3ab747260bbea8bb482d3864b52f6b3427b0`.
