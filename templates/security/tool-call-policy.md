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
- Approval event schema:

## MCP / Plugin Readiness

- Exposure inventory:
- Input/output schema:
- Auth scope:
- Smoke or inspector evidence:
- Plugin manifest/profile binding:

## Allowed Actions

| Action | Allowed input | Allowed path/domain | Required validation | Audit field |
|---|---|---|---|---|
| read-file |  |  |  |  |
| write-file |  |  |  |  |
| bulk-write | affected_count limit, selector, dry-run summary |  | approval + postcondition |  |
| run-command |  |  |  |  |
| network |  |  |  |  |

## Deny Rules

- Deny unlisted commands.
- Deny writes outside declared paths.
- Deny unbounded selectors and bulk writes without affected_count, max limit, dry-run summary and explicit approval.
- Deny credential reads without owner and purpose.
- Deny non-allowlisted provider/base URL when tools are enabled.

## Guard Tests

| Case | Input | Expected decision | Evidence |
|---|---|---|---|
| allow-path |  | allow |  |
| deny-path |  | deny |  |
| deny-scope |  | deny |  |
| deny-unbounded-bulk |  | deny |  |
| postcondition-failure |  | deny |  |

## Rollback

- Disable step:
- Config restore point:
- Verification command:
