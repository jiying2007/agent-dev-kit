# ADK 10.0.0 PR #236 — independent AI source review

- Reviewer identity: `ai/chatgpt/gpt6-pr236-independent-20261104` (AI, separate from PR implementation context; **not** human or GitHub approval).
- Author/GitHub user: `jiying2007`. Owner policy: `.adk/review-policy.json` / `.adk/review-authorization.md`.
- Original review target: base `f9984ca91e6b511937137df0558d51d179ff2a8f`; implementation HEAD `354b7e2f3128ee23f2a1abedef2b36ca13e5401c`. The retained full GitHub PR unified diff contains **55 changed paths** and is bound by SHA-256 in the machine record.
- Scope: code and repository-source evidence only. Review of affected implementation, 55-path patches, 9 OpenAI metadata moves, removed language-only Skill identities, new typed Skill/content/commit tests, existing installer and rollback source, governance and Actions workflow source; **not** an in-person/native/runtime measurement.
- Evidence from exact implementation source: [Python matrix + security/deterministic](https://github.com/jiying2007/agent-dev-kit/actions/runs/41784159036), [CodeQL](https://github.com/jiying2007/agent-dev-kit/actions/runs/41784161626), [Dependency Review](https://github.com/jiying2007/agent-dev-kit/actions/runs/41784159397), [Platform](https://github.com/jiying2007/agent-dev-kit/actions/runs/41784159046). GitHub Actions job snapshots at review: Python 3.11 & 3.12 contract and full regression success, static security success, deterministic evaluation package success, CodeQL success, dependency review success, platform success. Main-only signed promotion job was **skipped on PR**, correctly.
- All observations are from GitHub connector reads; reviewer did not execute target-native software, provider models, a local full test suite, Codex CLI/Cloud, ChatGPT Work or hardware tests.

## Seven scoped conclusions

1. **Source / correctness: PASS.** Two language-only Skills and their registered Manifest/Profile identity are removed; canonical review and commit gates retain applicable behavior; the new checker is read-only and returns explicit errors. No unauthorized code/SCM mutation in the introduced code.
2. **Security: PASS (source-only).** Diff introduces no secret, executable hook or network access; checker only reads a bounded UTF-8 message file and prints JSON. Required security checks pass.
3. **Permissions: PASS (source-only).** Risk and permission escalation remains separate; routing tests check commit-format requests have `mutation_permission=deny`, device escalation remains explicitly authorized. No real target permissions were tested.
4. **Performance: PASS for governed source limits; runtime impact NOT VERIFIED.** Eight source-byte Profile ratchets preserve fail-on-growth, recorded budget increases and the team-core reduction; these bytes are not initial model context tokens/latency.
5. **Maintainability: PASS.** Two parallel language Skill identities and seven duplicated reference SOPs removed; nine metadata layouts normalized; the canonical support guidance keeps one review severity taxonomy. Long-term content structure validated by typed tests instead of minimum line counts.
6. **Testing: PASS for exact implementation SHA CI.** Python 3.11 & 3.12 full regression and contract, static-security, deterministic eval package, CodeQL/dependency/platform jobs succeed; tests cover content v2, metadata, mutation denial and syntax validation. Future evidence-commit SHA requires fresh checks.
7. **Migration and recovery: PASS for source contract with target migration unverified.** Transactional installer does **not** silently prune omitted managed assets. The current 9→10 direct plan returns `needs-review` on retired installed paths. Correct path is verify exact trusted 9.x source/receipt and old files+modes, rollback under lock, then fresh exact-10.0.0 plan/apply and new receipt; preserved drifted/unmanaged assets cause conflicts. Actual target migration was not performed.

## Bounded findings and limitations

- **minor / accepted-risk — synthetic retirement fixture**: the new install-upgrade regression retires `adk-after-action-review` from an isolated fixture, not the actual two 9.0 Chinese Skills. Existing inventory/rollback contract code was additionally read; exact old 9.x live target state remains unobserved.
- **minor / accepted-risk — source-byte performance**: `profile_context_ratchets.json` measurements and fixed source-byte limits do not prove token cost or provider-model runtime latency. Do not label native/effect/M5 as pass.
- **minor / accepted-risk — deferred promotion**: fresh source-bound AI and Harness evidence itself must pass new HEAD CI before Ready/merge. GitHub immutable v10.0.0 tag, Sigstore, release and downstream Root pin are not proven by PR CI.
- Reviewer self-declared identity and content hashes are not cryptographic third-party authentication. Connected GitHub credential equals PR author's GitHub login; **no separate GitHub APPROVE may be claimed**. This record uses owner-delegated AI policy rather than representing human independent approval.
- The review does not authorize or attest live device M5, `~/.codex`, installed target/receipt, real model-provider runs or paid resources.

Disposition: **Spec PASS / Quality PASS for the exact pre-evidence implementation source**; no open blocker/major found within the reviewed source scope. Promotion must remain gated on fresh CI, reviewer evidence consistency, ruleset and signed main release.
