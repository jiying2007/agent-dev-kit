# MCP Governance

- Transport is local stdio and tool access is read-only by default.
- Any external write requires explicit approval and an allowlist entry.
- Credentials come from an environment variable or runtime secret manager.
- Failure falls back to local documentation; no command is retried indefinitely.
