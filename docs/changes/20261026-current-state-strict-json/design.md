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
