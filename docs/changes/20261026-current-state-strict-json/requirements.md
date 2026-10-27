# Current-state strict JSON

The read-only `goal state-check` must reject ambiguous duplicate keys, nonfinite or overflowing numerics, and excessive JSON nesting. Reuse the existing canonical `strict_json` implementation without changing the 8 KiB default, schema/field checks, input-bytes hash, `completion_allowed=false`, or referenced-evidence verification boundary.

No Native G21, effect G22, LTA-04, Product M5, runtime import or live apply is authorized by state hygiene alone.

Reject unsafe leaf inputs (FIFO, directory and symlink) with a structured failure using the canonical descriptor-based bounded reader. Preserve `state_sha256=null` for unsafe or over-budget inputs and the exact source-byte digest for valid inputs.

Reject symlinked parent directories as well as the file leaf; state-check accepts path input but must not silently follow path aliases. This check is preflight-only and does not certify a concurrent malicious writer.

Reject invalid Unicode scalar values (unpaired UTF-16 surrogate escapes) in JSON object keys and any nested string value; a properly paired surrogate escape is accepted as its real Unicode code point. State hygiene must not PASS escaped values that cannot be represented in UTF-8.

The Harness readiness contract is an input to governance decisions and must use the canonical bounded strict JSON reader (256 KiB ceiling), reject symlink ancestry and non-regular files, and never leak invalid source values in parser errors. Preserve all seven dimensions and current review authority; a stricter loader does not itself renew review evidence.

The real independent review of ADK #226 found two further source hardening requirements: reject ambiguous `mcpServers` JSON before secret scanning, and bind Harness text evidence reads to a bounded regular file descriptor instead of separate `stat/read_text`. Preserve fail-closed security findings, redact unsafe values, and do not regenerate or imply an independent review PASS without actual separate reviewer execution.

Review-backed requirement: the MCP permission scanner must detect command/args literal credential sinks even if the dependency is pinned and permissions are otherwise declared. Unsafe literal arguments block readiness; malformed arguments require review. All evidence references must redact arbitrary JSON keys and MCP server names, not only secret values. Preserve canonical environment/secret-manager reference handling and the independent Harness review gate.

MCP permission source scanning must detect bounded sensitive components in composite header/env names anywhere, and inspect Bearer/Basic credential-bearing header values even under noncanonical header names. Single-dash secret flags and empty sensitive assignments must fail closed, without treating source scanning as runtime authentication or field evidence.

The Harness MCP scanner must inspect credential-bearing values in remote URL/URI/endpoint query parameters and userinfo, as well as assignments embedded in non-sensitive env value strings. Non-string command and malformed env/headers/url shapes must return needs-review rather than PASS. Never log raw credential-bearing input, and do not claim native runtime credentials were tested.

Reject all unsafe MCP config shapes during discovery: symlink, FIFO, nonregular and directory candidates with `.mcp.json` / `mcp.json` names must be reported as needs-review, never incorrectly disappear into N/A. Bound the retained unsafe evidence list by the existing max_configs and use only opaque source-name evidence labels; do not open the special files. URL userinfo must separately validate encoded username and password, and malformed/overflowed or unsupported URL ports/schemes must fail closed.
