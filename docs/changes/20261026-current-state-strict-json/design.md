# Design and rollback

Parse the existing one-read bounded byte snapshot with `strict_json.loads(raw, max_bytes=max_bytes)` and catch its `ValueError` subclass through the existing schema-invalid branch. Keep oversize as a structured `current-state-byte-limit` outcome. Use the canonical parser depth threshold rather than inventing a second limit. Add adversarial unittest cases for top-level duplicate keys, NaN, numeric overflow and >64-level nesting.

Rollback source, regression, docs and synchronized patch SemVer together through a protected PR. Do not move a signed release tag or reuse historical product evidence.
