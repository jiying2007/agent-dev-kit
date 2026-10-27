# Design and rollback

Parse the existing one-read bounded byte snapshot with `strict_json.loads(raw, max_bytes=max_bytes)` and catch its `ValueError` subclass through the existing schema-invalid branch. Keep oversize as a structured `current-state-byte-limit` outcome. Use the canonical parser depth threshold rather than inventing a second limit. Add adversarial unittest cases for top-level duplicate keys, NaN, numeric overflow and >64-level nesting.

Rollback source, regression, docs and synchronized patch SemVer together through a protected PR. Do not move a signed release tag or reuse historical product evidence.

## File input safety

Use `strict_json.read_bytes(path, max_bytes=max_bytes, regular_only=True)`: `O_NONBLOCK` ensures a FIFO cannot stall before its opened descriptor is checked, `O_NOFOLLOW` rejects leaf symlinks, and `fstat` validates file type. Map the existing size-budget failure to `current-state-byte-limit`, and unsafe-source failures to `current-state-input-invalid`. This does not claim parent directory isolation against concurrent renames/writers.

State-source path preflight walks every lexical parent to reject symlink aliases, matching existing consumer intake policy. It is a preflight guard rather than atomic protection against concurrent parent replacement. The opened descriptor still provides leaf regular-file/O_NOFOLLOW/O_NONBLOCK checks. Test an otherwise valid JSON reached through a symlinked directory.

## Unicode scalar validation

Python's default JSON decoder accepts syntactically escaped lone UTF-16 surrogates and returns strings that cannot be encoded to UTF-8. Reuse the same canonical strict decoder for all callers and iterate the bounded parsed value tree, rejecting such string values and object keys with a sanitized StrictJSONError. This does not echo user-provided keys or values. Proper surrogate pairs decode to valid Unicode and remain accepted.

## Harness contract input authority

The Harness contract parser previously followed symlinks and read unbounded JSON. Route it through the same strict JSON decoder with descriptor-based regular-file checks, a 256 KiB hard limit and lexical parent-component symlink preflight. Continue enforcing all existing schema and review semantics. A signed review must bind the changed readiness_evidence.py validator fingerprint; this source-only repair is not an independent delegated review. Symlink preflight is not a guarantee against concurrent parent replacement.

## Bounded Unicode scan cost

Only escaped surrogate code units (JSON `\\uD800`-`\\uDFFF`, case-insensitive hex) can enter a decoded string as lone surrogates: direct invalid UTF-8 is already rejected at decode, while direct `str` input is encoded as UTF-8 before parsing. Check the bounded raw byte payload for those escapes and perform the existing complete parsed-tree Unicode scalar validation only when a possible surrogate escape appears. False-positive matches inside escaped backslash text are safe, because the final tree check will accept actual valid scalar text. Test the fast path and valid literal backslashes, and preserve failure for real escaped lone surrogates.

## Independent review blocking findings (2026-10-27)

A separate independent code review of exact PR HEAD identified a pre-existing risk: `readiness_tools._evaluate_tools` used Python `json.loads`, allowing repeated `mcpServers` keys to hide earlier sensitive configuration before `_walk_json`. Use `strict_json.loads` instead and fail closed with `invalid_mcp_json`; reject NaN, overflowing float and escaped lone surrogates without leaking input into blockers.

A second finding concerns `RepositoryIndex.read_text`: its `stat()` followed by independent `Path.read_text()` may read a grown/replaced input beyond the scan budget. Capture bytes once using the existing `strict_json.read_bytes(..., regular_only=True)` (O_NOFOLLOW, O_NONBLOCK, fstat regular file, max_bytes+1), reject symlink ancestry before opening, and decode UTF-8 strictly. This eliminates the unbounded separate read; it does not prove atomic parent directory isolation during concurrent renames.

The source and test changes invalidate the previous 8.1.1 delegated review. New independent review of the current head and changed validator/runtime source is still mandatory before merging; do not treat a CI pass on specific code tests as a Harness receipt.

## MCP command/args and evidence-reference redaction

Independent reviewer #5662021181 of exact HEAD 15729db306e789b4871a865a102e862a350de6d0 found plaintext credential arguments (for example, a pinned package with a token parameter) were not covered by dictionary-key-only secret checks. The source-only fix checks credential-named assignments, inline/split flags and Authorization/Bearer header strings in command and args. Existing SECRET_REFERENCE remains the authority for environment placeholders; malformed flags fail closed separately. These are bounded static diagnostics, not runtime execution or a full shell interpreter.

All recorded MCP blocker references use deterministic sorted server ordinals and opaque field positions, not user-controlled server names or nested JSON keys. The tracked config file path and category remain visible, without printing credential values. The test matrix includes normal managed references and adversarial literal CLI arguments, malformed flags and dynamic key/name redaction. The 8.1.1 reviewer record does not become valid through these repairs: real new source-pinned independent Spec/Quality review remains a separate requirement.

## Exact-head test correction

PR CI 40447876786 exposed two genuine failures in the newly added MCP CLI tests: `--env=TOKEN=value` was only checked as an `env` outer assignment, hiding the nested `TOKEN` sink; and long all-caps fixture literals triggered the repository's production security scanner. The assignment matcher now uses bounded zero-width lookahead so both the outer flag and nested credential name are inspected. Negative fixtures use short clearly dummy values while preserving real malicious semantics. This does not weaken the repository scanner or remove the test cases. The separate stale Harness source review gate remains closed until an actual independent review of this exact source.

## Compound secret keys and HTTP header semantics

A source-pinned independent audit of HEAD 9394a904df3f697fcb0e9b000915a6416d2313b2 found a reproducible false PASS for `private-token-demo_value` and an additional static false PASS path for nonstandard headers carrying Bearer/Basic plaintext. Recognize whole sensitive components anywhere in composite keys (including camelCase), plus credential-bearing header values independent of key spelling. Keep existing compact-match behavior, accept managed environment references including Basic placeholders, reject single-dash literal flags and malformed empty assignments. All issue refs remain opaque. These checks do not execute MCP binaries or constitute complete shell parsing. A new source identity again requires an independent seven-dimension Harness review.

## Remote URL, env value and input schema authority

Independent AI review #5662670792 of exact source a5d6eb55d6ba04b8d440f56d45c9c004f503536e found credential-bearing HTTP/SSE URL query/userinfo fields and indirect env values could bypass key-based scanning; non-string MCP commands could be misclassified as valid source inputs. Reuse the same static literal-credential detector for any env descendant scalar, enforce string mapping structure for env and headers, and reject non-string command values. URL/URI/endpoint sources are bounded (8KiB, 128 query delimiters) and decoded using Python's stdlib URL parser; query/fragment credentials and password userinfo are checked against the existing canonical managed secret-reference policy. Invalid URL types or syntax fail closed as needs-review. Opaque error refs continue to exclude raw server names, query text and secret values. Tests prove literal and safe placeholder URLs/indirect env values, plus unsupported input structures; these checks are static and do not authenticate remote servers. The source change again invalidates earlier review records.

## URL and special-file source inventory findings

The independent reviewer of HEAD fef217a16dbb91f1162e8c970187a1e65f10e045 identified a URL userinfo bypass (encoded credential assignment in the username paired with an environment password) and malformed ports allowed through `urlsplit` without accessing `.port`. Validate both username and password after percent decoding, require managed references for embedded identities, reject invalid schemes, hostnames and ports (including zero) and retain the original bounded parser and opaque errors.

RepositoryIndex previously dropped symlinks and non-regular MCP config paths from index population, permitting tool_and_permission_boundary to return N/A although a named configuration existed. Keep a separately bounded set of unsafe config names while refusing to read the target, including special files and directories. The permission scanner must return needs-review and structured blockers for those names, with no user path secrets copied into refs. This is scan coverage hardening, not a new runtime MCP verifier. Current source review records must be renewed by an actual independent reviewer once code changes stabilize.

## Authority delimiters and missing credential semantics

Independent source review #5663083519 of HEAD `8602d19271391519e656bf563edefe661ebc426b` found that a source comparison against two backslash characters failed to reject one literal backslash in a URL authority, and that `access_token=` was incorrectly treated as a safe managed reference. Reject individual literal backslashes, encoded authority separators, malformed percent escapes and empty sensitive query/fragment/userinfo values, while retaining canonical environment placeholders. Explicit empty credential declarations require `needs-review`; literal credential values remain `blocked`. This is static input validation, not HTTP transport authentication. Exact-source independent review and unchanged Harness gates remain mandatory.

Raw URL strings must be screened before any stdlib URL normalization that can discard control characters. Any explicitly present credential name with no value, including indirect env string assignment and headers, is malformed and must fail closed as needs-review; allow truly managed environment references and never echo raw input. Source fixes do not create the independent reviewer record required for Harness seven dimensions.
