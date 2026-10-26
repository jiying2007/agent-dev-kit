# Current-state strict JSON

The read-only `goal state-check` must reject ambiguous duplicate keys, nonfinite or overflowing numerics, and excessive JSON nesting. Reuse the existing canonical `strict_json` implementation without changing the 8 KiB default, schema/field checks, input-bytes hash, `completion_allowed=false`, or referenced-evidence verification boundary.

No Native G21, effect G22, LTA-04, Product M5, runtime import or live apply is authorized by state hygiene alone.

Reject unsafe leaf inputs (FIFO, directory and symlink) with a structured failure using the canonical descriptor-based bounded reader. Preserve `state_sha256=null` for unsafe or over-budget inputs and the exact source-byte digest for valid inputs.
