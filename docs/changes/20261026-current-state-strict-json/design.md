# Design and rollback

Parse the existing one-read bounded byte snapshot with `strict_json.loads(raw, max_bytes=max_bytes)` and catch its `ValueError` subclass through the existing schema-invalid branch. Keep oversize as a structured `current-state-byte-limit` outcome. Use the canonical parser depth threshold rather than inventing a second limit. Add adversarial unittest cases for top-level duplicate keys, NaN, numeric overflow and >64-level nesting.

Rollback source, regression, docs and synchronized patch SemVer together through a protected PR. Do not move a signed release tag or reuse historical product evidence.

## File input safety

Use `strict_json.read_bytes(path, max_bytes=max_bytes, regular_only=True)`: `O_NONBLOCK` ensures a FIFO cannot stall before its opened descriptor is checked, `O_NOFOLLOW` rejects leaf symlinks, and `fstat` validates file type. Map the existing size-budget failure to `current-state-byte-limit`, and unsafe-source failures to `current-state-input-invalid`. This does not claim parent directory isolation against concurrent renames/writers.

State-source path preflight walks every lexical parent to reject symlink aliases, matching existing consumer intake policy. It is a preflight guard rather than atomic protection against concurrent parent replacement. The opened descriptor still provides leaf regular-file/O_NOFOLLOW/O_NONBLOCK checks. Test an otherwise valid JSON reached through a symlinked directory.
