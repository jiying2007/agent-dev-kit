# Harness repository-source review — 2026-10-21

Owner/delegator: `leiwenjun`. Implementing and record-assembly actor: `ai/root`. Actual independent Spec reviewer: `ai/root/external_methods`; actual independent Quality reviewer: `ai/root/native_evidence_audit`. Both reviewers read the current source and remained read-only with respect to the repository. Their scratch reports are preserved byte-for-byte under `docs/changes/20261021-harness-utc-date/evidence/`.

## Actual scope and source binding

The target is the working tree based on `42ae95d146ceb441ff91ea33dbbed581c33de305`. Both reviewers read all sixty current source files, the unchanged delegated policy/authorization and three validator modules, the UTC implementation/test increment, retained historical findings, and actual current red/green evidence. The independently matching sixty-file manifest SHA-256 is `ae0a3b4907e00b666f8d875358d07693a9fb757b45a99172314676f3c2ed0092` (path/bytes/sha256 records, sorted by path, JSON keys sorted, compact UTF-8, no trailing newline).

Only README and `readiness.py` differ from the prior sixty-source binding. The old October 20 receipt remains intact and correctly fails against these changed sources. This new review does not alter its timestamp, fingerprints, findings or result.

The canonical new receipt also binds the two independently reviewed UTC regression files, for 62 source plus 2 evidence references within the unchanged 64-reference budget. Its expanded source-manifest digest is `983cbca1e3d88df34052c8a5fd6ba48403373e81b588bb8893469042a775e613`; the original sixty-file digest above retains its original scope.

## Actual independent verdicts

- Spec completed at `2026-10-21T01:56:08Z`: PASS, no open blocker or major.
- Quality completed at `2026-10-21T01:55:04Z`: PASS, no open source blocker or major.
- The later aggregate confirmation is recorded in the retained Spec aggregate report and the new canonical receipt. It follows the actual Quality report rather than predating it.

| Dimension | Current source assessment | Reviewed basis |
| --- | --- | --- |
| context_legibility | pass | Short instruction index, detailed operating rules, current README and bounded context policy retain distinct source, component, runtime and product authorities. |
| spec_and_execution_contract | pass | Requirements/tasks/negative evidence, one canonical review lifecycle, source fingerprints and separate author/reviewer identities remain enforceable. |
| tool_and_permission_boundary | not-applicable | The real repository scan finds no applicable live MCP configuration. Structured permission, pinning and credential rejection paths remain in source. |
| state_and_knowledge_continuity | pass | Historical state, provenance and deliberate knowledge/memory compilation remain traceable without rewriting prior qualification. |
| verification_review_and_eval | pass | Deterministic negative tests, supported-Python CI, independent review and real execution evidence remain separate authorities. |
| recovery_and_rollback | pass | The previously repaired bounded archive restore, private staging, atomic commit/compensation and eight filesystem-test sources remain intact. |
| freshness_and_entropy_control | pass | The public entry samples one UTC day; all dimensions receive it. Ninety-day freshness, zero future tolerance and rejection of explicit gate time travel remain unchanged. |

## Findings resolved in this increment

`UTC-READINESS-DAY-001` (major): canonical UTC review dates were compared with the host local calendar. The minimal production entry fix uses `datetime.now(timezone.utc).date()`. Deterministic tests cover local dates on both sides of UTC and the delegated Harness chain.

`UTC-HARNESS-TEST-DAY-001` (minor): two shell test clocks could disagree with the UTC gate. The current-pass fixture date and stale-date expectation now use UTC. This does not change validator fingerprints or weaken date checks.

The old receipt's source rejection is an expected delivery prerequisite, not permission to refresh its hashes. A genuinely new record must be validated with its new metadata pointer. The source review itself does not assert that this later gate has already passed.

## Execution evidence and limits

The author's actual 45-test run completed at `2026-10-21T01:39:24.702218Z`, exit 0; both reviewers independently read and hashed its original receipt/stdout/stderr. They did not claim to have executed that suite. The earlier complete 99/101 failure and deterministic UTC red run remain preserved. Separate archived-review compatibility checks found ADK 5/5 valid and Root 3/3 ready under unchanged validator fingerprints.

Six applicable source dimensions pass and the tool dimension remains N/A. `field_evidence_status` remains `not-verified`. This review neither authenticates a human/platform identity nor supplies Native/provider execution, G22 measurement, LTA field events, Product M5 qualification or release authority. The actual current-date canonical gate, complete regression, protected CI, immutable component release and exact Root promotion require their own observable results.
