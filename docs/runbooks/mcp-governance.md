# MCP Governance

MCP is an external capability boundary for ADK. ADK records MCP declarations and audit rules; it does not silently enable external tools or write runtime config.

## Required Fields

- server name, transport, command or URL
- enabled tools and disabled tools
- approval mode and per-tool override
- auth boundary and secret policy
- dry-run path, rollback path and evidence owner

## Gates

1. Register MCP candidates as report-only by default.
2. Run security and supply-chain review before enabling external writes.
3. Keep tool descriptions action-oriented and explicit about read/write/destructive behavior.
4. Require runtime smoke evidence before production use.
