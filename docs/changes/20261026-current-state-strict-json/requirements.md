# Current-state strict JSON

The read-only `goal state-check` must reject ambiguous duplicate keys, nonfinite or overflowing numerics, and excessive JSON nesting. Reuse the existing canonical `strict_json` implementation without changing the 8 KiB default, schema/field checks, input-bytes hash, `completion_allowed=false`, or referenced-evidence verification boundary.

No Native G21, effect G22, LTA-04, Product M5, runtime import or live apply is authorized by state hygiene alone.

Reject unsafe leaf inputs (FIFO, directory and symlink) with a structured failure using the canonical descriptor-based bounded reader. Preserve `state_sha256=null` for unsafe or over-budget inputs and the exact source-byte digest for valid inputs.

Reject symlinked parent directories as well as the file leaf; state-check accepts path input but must not silently follow path aliases. This check is preflight-only and does not certify a concurrent malicious writer.

Reject invalid Unicode scalar values (unpaired UTF-16 surrogate escapes) in JSON object keys and any nested string value; a properly paired surrogate escape is accepted as its real Unicode code point. State hygiene must not PASS escaped values that cannot be represented in UTF-8.

The Harness readiness contract is an input to governance decisions and must use the canonical bounded strict JSON reader (256 KiB ceiling), reject symlink ancestry and non-regular files, and never leak invalid source values in parser errors. Preserve all seven dimensions and current review authority; a stricter loader does not itself renew review evidence.

The real independent review of ADK #226 found two further source hardening requirements: reject ambiguous `mcpServers` JSON before secret scanning, and bind Harness text evidence reads to a bounded regular file descriptor instead of separate `stat/read_text`. Preserve fail-closed security findings, redact unsafe values, and do not regenerate or imply an independent review PASS without actual separate reviewer execution.
