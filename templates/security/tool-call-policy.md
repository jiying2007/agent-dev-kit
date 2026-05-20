# Tool-call Policy Template

## Scope

- Tool/server:
- Owner:
- Runtime:
- Review date:
- Expiry or next review:

## Trust Boundary

- Provider/base URL:
- MCP command and args:
- Credential source:
- Sandbox/approval policy:
- Hook involvement:

## Allowed Actions

| Action | Allowed input | Allowed path/domain | Required validation | Audit field |
|---|---|---|---|---|
| read-file |  |  |  |  |
| write-file |  |  |  |  |
| run-command |  |  |  |  |
| network |  |  |  |  |

## Deny Rules

- Deny unlisted commands.
- Deny writes outside declared paths.
- Deny credential reads without owner and purpose.
- Deny non-allowlisted provider/base URL when tools are enabled.

## Guard Tests

| Case | Input | Expected decision | Evidence |
|---|---|---|---|
| allow-path |  | allow |  |
| deny-path |  | deny |  |

## Rollback

- Disable step:
- Config restore point:
- Verification command:
