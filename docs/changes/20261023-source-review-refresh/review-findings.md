# Independent source refresh review

Reviewer: `ai/root/architecture_audit` (AI, independent of implementer).
Author/implementer: `ai/root`.
Subject: `20261023-source-review-refresh`.

Spec: **PASS**. Quality: **PASS**. No unresolved blocker or major finding within
the reviewed metadata and static crosswalk scope.

## Exact scope and provenance

The retained implementation is
`70094158251f3a11eaceee5d95cb63dfcea1e895`, parent
`c06fd629fa9a08f3079e7a606f45e65fcccbfc28`, tree
`5bdab3551e6940e53ce5bdc9d3eedc4de678478d`. The complete base-to-head binary-capable
patch is retained as `evidence/original.patch`. That commit also contains a small
release implementation follow-up, which has a separate independent reviewer and
is outside this review's verdict. The present verdict covers the two changed
manifests and this source-review change's contracts and evidence.

The reviewer personally researched the registered primary sources and designed
the minimal correction before the author applied it. The reviewer did not change
either production manifest. Requirements, design, tasks and the actual manifest
diff were reread after implementation. The independently reconstructed expected
JSON documents match both actual documents in full, so every other field,
source date, source ID and authority remains unchanged. Related gate and regression
source bytes also match the original implementation commit.

## Findings resolved by the author

1. **Expired active source reviews.** The full inventory found two expired entries
   among the 11 active ecosystem sources. The actual baseline gate failed on
   precisely those two entries. Both were rereviewed from primary sources before
   their review metadata was refreshed. The 30-day next-review interval is a local
   scheduling choice. The expiry gate and current clock checks remain unchanged.

2. **AST05 semantic drift.** The fixed OWASP source names AST05 as an external
   instruction risk, whereas the old local crosswalk assigned a parsing risk to
   that ID. The author synchronized AST05 and retained every original parser
   surface, control and evidence requirement under AST04. An independent comparison
   against the pinned upstream table now matches all ten risk names.

3. **Incomplete license and source identity metadata.** The OWASP license was
   actually read at the fixed revision and is recorded as CC-BY-SA-4.0. The paper's
   formal title, fixed v2 identity and arXiv distribution-license limitation are
   now explicit. Its observational findings support a maintenance method, not an
   assertion of local use or measured benefit. No third-party body, dataset,
   replication code, Skill package or runtime was imported.

## Independent verification

| Check | Observed result |
|---|---|
| Full actual JSON versus preimplementation proposal | Exact match for both manifests |
| Risk names versus fixed upstream `top10.md` | All 10 match |
| Original parser surfaces, controls and evidence | All retained under AST04 |
| Ecosystem governance | 553 checks pass; 11 sources; runtime disabled |
| Existing ecosystem regression | Pass, including its strict-validation invocation |
| External reference binding regression | 7 tests pass |
| Official source governance | 69 sources pass on the declared current UTC+08:00 date |
| Existing Harness receipt validator | Pass with the unchanged original record |
| Current Harness gate | Exit 0, six applicable dimensions pass and one not applicable |
| Source digests before and after every executed check | No drift |

Actual arguments, timings, outputs and byte digests are in
`evidence/independent-review-execution.json`; exact proposal comparisons,
source-authority snapshots and the unchanged Harness validation are in
`evidence/independent-review-probes.json`. The original Harness record remains
`harness-source-20261023-8.0.39.json`, reviewed at
`2026-10-23T12:17:59.467787Z`, SHA256
`9ceb000c7ed70bdd3e9fc3be29abde0da62e5ea1d6583c6b37cc88971a72f9f7`.
Neither changed manifest is one of its 61 bound source files. The current gate
confirmed that retaining that record is valid; its dates were not moved.

## Source evidence and limits

Primary source identities and returned byte hashes are in
`evidence/primary-source-observations.json`. All seven retrieved GitHub text files
were checked against their reported Git blob identity. The actual review examined
the relevant README/risk table sections, the complete AST05 and license, and the
publication pointer. The full linked OWASP whitepaper was not reviewed.

Primary references:

- [OWASP AST05 at the observed commit](https://github.com/OWASP/www-project-agentic-skills-top-10/blob/d6f7d7d0de314f52a83a85d1828e06ab096e595c/ast05.md)
- [OWASP license at the observed commit](https://github.com/OWASP/www-project-agentic-skills-top-10/blob/d6f7d7d0de314f52a83a85d1828e06ab096e595c/LICENSE.md)
- [Paper v2 metadata](https://arxiv.org/abs/2607.00911v2)
- [Paper v2 HTML](https://arxiv.org/html/2607.00911v2)
- [Declared arXiv distribution license](https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html)

The paper review covered its methods, maintenance findings and stated validity
limits, without downloading its replication package. Publisher raw bytes were
not obtained, so no arXiv content digest is invented. Direct network fetches were
unavailable in the sandbox; official web rendering and fixed GitHub connector
reads supplied the evidence. The 69 other official sources were checked for
current metadata validity, not semantically recertified. The two old Harness
citation dates remain unchanged, including the user excerpt with no source URL.

This is independent AI source review. It is not human attestation, security
certification, target runtime qualification, field-effect evidence, protected CI
success or release authorization. Full integration and publishing remain separate
delivery observations. Observations were collected across reads and commands;
they are not an atomic snapshot of the entire repository.
