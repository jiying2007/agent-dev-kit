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
