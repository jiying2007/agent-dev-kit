# ADK 8.1.2 — independent AI Spec / Quality and seven-dimension Harness source review

- Review execution: GPT-6 AI, separate review run `77d99976-7eec-8330-ae9c-a132419c0ce6` (platform task started `2026-10-27T14:43:24.360557Z`; verified with existing Automations.peek).
- Implementation author actor: `ai/root`. Repository connection account `jiying2007` is a GitHub write channel only, **not** the reviewer, human Owner, second agent, external independent provider, or signer.
- Source-pinned original PR #226 implementation HEAD: `d84607a5ceb6e0196edbf88f3b63f8b43db21a38`; protected main and PR base: `95997abb318144aa6433fb40af4b2f0f1f4ceee4`.
- Reviewed complete GitHub PR diff: 18 changed paths, 85,452 per-file patch characters, no missing patches. Independently read current full `readiness_tools.py` (525 lines), `readiness_evidence.py` (444), `strict_json.py` (136), `planning_state.py` (84), `review_evidence.py` (283), `readiness.py` (468), `tests/test_strict_json.py` (812), `tests/test_harness_readiness.sh` (366), current requirements/design/tasks, AGENTS/README, policy/authorization, contract, metadata, ownership, recovery and MCP governance runbook; checked remaining patch files for version scope.
- Original 8.1.1 review record: exactly 62 repository source refs + 1 historical review evidence ref. Full untruncated Git tree comparison between main and audited HEAD: all 62 refs exist, 58 identical Git blobs, 4 changed (CHANGELOG, README, manifest, readiness_tools). Git blob ID is used **only** for byte-identity comparison; SHA-256 below uses separately fetched UTF-8 bytes.

## Independent Spec verdict: PASS — repository source and static governance scope only

The read-only goal state-check now uses the canonical strict JSON loader; duplicate keys at any level, NaN/Infinity/overflow, excessive nesting, malformed/lone-surrogate Unicode are rejected. Positive surrogate pairs remain valid. FIFO/directory/leaf symlink rejection is bound to one regular-file descriptor with O_NONBLOCK/O_NOFOLLOW/fstat and max_bytes+1, preserving the 8 KiB default and the source-byte digest and `completion_allowed=false`. Parent symlink rejection is **preflight only**, not atomic against hostile concurrent parent renames. Harness contract input is bounded to 256 KiB with the same safe reader. There is no runtime import, MCP execution, product approval or field qualification in this static review.

For MCP static configuration source scanning, independently traced full `_evaluate_tools` branches. Strict JSON fail-closes duplicate `mcpServers`, nonfinite numbers and malformed structures. Literal command/args split/inline tokens, indirect `env.APP_OPTIONS` assignments, sensitive or composite/camel-case keys, arbitrary-header Bearer/Basic, URL query/fragment/userinfo and encoded credentials become blocked or needs-review; managed `${DEMO_TOKEN}` and related canonical placeholders remain positive. Original URL text is checked before urlsplit normalization; malformed authority separators/backslashes/ports/percent escapes and explicitly empty declared credentials fail closed. Unsafe MCP symlink/FIFO/directory configurations enter the bounded unsafe inventory and cannot disappear into tool N/A. Dynamic server names and JSON keys are replaced with ordinal references. Review did not execute any MCP server, shell command or authentication flow.

The latest candidate repairs the previous concrete split-flag false PASS: `readiness_tools.py:121–128` checks `not args[position + 1].strip()`, so `["safe-package@1.2.3","--token"," "]` and tab-only variants now yield malformed `needs-review`. Corresponding complete-scanner tests are in `tests/test_strict_json.py:194–205` and were exercised in native Python 3.8/3.11/3.12 GitHub regression jobs. The legitimate `["--token","${DEMO_TOKEN}"]` case still passes within declared permission metadata.

## Independent Quality verdict: PASS — reviewed source semantics, not release qualification

No unresolved major or blocker was found **within the declared bounded repository-source/static-scanner trust boundary**. Previous source-review MAJORs have explicit scoped code/negative-test corrections: duplicate keys; bounded file capture; CLI literals and opaque refs; composite/header secrets; URL/indirect-env literals; userinfo/ports; special files; authority/empty credentials; raw controls; and whitespace-only split token values. The evaluator is read-only, produces structured sanitized findings and caps files/configs/blockers; over-budget or unreadable inputs do not become source PASS. This is not a proof of a complete shell grammar, URL client normalization, concurrent hostile filesystem changes or live credential validation.

Exact original implementation HEAD native CI: `agent-dev-kit-ci` [40523530066](https://github.com/jiying2007/agent-dev-kit/actions/runs/40523530066) completed failure; all Python 3.8/3.11/3.12 **contract** and static-security jobs passed, as did independent CodeQL [40523530001](https://github.com/jiying2007/agent-dev-kit/actions/runs/40523530001), dependency review [40523529745](https://github.com/jiying2007/agent-dev-kit/actions/runs/40523529745) and platform [40523530072](https://github.com/jiying2007/agent-dev-kit/actions/runs/40523530072). Each Python-version regression was 100/101 with `test_strict_json` PASS and `test_harness_readiness` FAIL because obsolete 8.1.1 delegated review source/validator fingerprint is rejected (`invalid_delegated_review`). Deterministic eval therefore failed its prerequisite; promotion evidence was skipped. This is a **real non-green gate**, not ignored or reclassified as CI success. Fresh evidence/metadata source identity and a new exact-head successful CI are required after this review; none of this evidence authorizes immediate merge.

## Harness seven dimensions — scoped, independent source judgments

1. `context_legibility`: PASS source assessment — root AGENTS (39 lines), README, linked operating rules.
2. `spec_and_execution_contract`: PASS source assessment — canonical requirements/design/tasks, negative regression and acceptance artifacts.
3. `tool_and_permission_boundary`: source contract/scanner reviewed with no current unresolved MAJOR. For this repository actual raw MCP config is **not-applicable**, **not** universal MCP safety PASS; generic fixture positives/negatives are static only.
4. `state_and_knowledge_continuity`: PASS source assessment — governed state.yaml/PROGRESS and docs/runbooks.
5. `verification_review_and_eval`: PASS source assessment — tests, .github CI, reproducible validation commands, exact versioned job logs and explicit stale-review failure.
6. `recovery_and_rollback`: PASS source assessment — scripts/backup-rollback.sh, docs/runbooks and change rollback boundary; no destructive restore executed.
7. `freshness_and_entropy_control`: PASS source assessment — format/catalog checks, OWNERS and .github/CODEOWNERS, bounded scan and fresh dated review.

**Important:** Before a properly source-bound new record and metadata are validated, current *effective* Harness statuses are still 7/7 needs-review. Above verdicts are a fresh independent semantic source review, not the old effective gate result or a human signature.

## Actual SHA-256 content fingerprints (not Git blob IDs)

- `.adk/review-policy.json` = `f6c7571084b3f36e12e1fea1e71a46108a54835ba438b189f727a20ee88e0a24`.
- `.adk/review-authorization.md` = `1594e628184cb0e4ad6c669bf5ce39dcb1f333d03d0798bebb080856e703cda5`.
- `src/agent_dev_kit/review_evidence.py` = `73d85e864a3da125bf94808f19616f52150751a94ccc729ac66f66d2576b8808`.
- `src/agent_dev_kit/strict_json.py` = `72f06f4dcaebfed83bd1ae9876e38d4f7d82d8a1473b40b66beffb6338ee94a5`.
- `src/agent_dev_kit/readiness_evidence.py` = `6fdfd5bea3ee097ac21d2b2ab469378c8c84f78856061b680ebb0c5f9d726778`.
- Changed 8.1.1 source refs: `CHANGELOG.md` = `14c3d348d3f968b938c39e43723cfb23f88142a5ec8bd5873fe371142f203809`; `README.md` = `2b32d628e724e10ee987896959786528057034fbd78f9e2fd5602b861b9f1aab`; `manifest.json` = `9b1858e2df22c2fc6fd106952263c78120602cc932d028cc0ff46f2bc5f39f5d`; `src/agent_dev_kit/readiness_tools.py` = `2ecdfd21eb665d45ff2ae279ffcf05eb01f09edfce391b1db105a03d15fd1cb5`.
- 58 unchanged source refs use the 8.1.1 byte SHA-256 only after full-tree Git blob identity equality was independently rechecked; no claim of rereading each of those 58 files line by line.

## Limitations and release boundary

- No Codex Cloud/CLI, ChatGPT Work, paid API, independent human Owner, signing identity, live MCP server, target runtime, native G21, G22 measurement, LTA-04 or Product M5 qualification was used or invented.
- Python 3.8/3.11/3.12 test results were **read from actual GitHub Actions**; the reviewer did not personally execute three interpreters locally. Isolated source semantic checks and complete source reading are distinct from such dynamic integration evidence.
- An updated review record and `.adk/harness-readiness.json` are mechanical evidence bindings only, not a relaxation of gate logic. They must be validated on their new HEAD. Official expected-head squash may only follow all required fresh checks being green, then distinct fresh-main and immutable signed release evidence, then Root managed exact-source promotion.
