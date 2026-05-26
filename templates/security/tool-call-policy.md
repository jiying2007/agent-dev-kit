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
- Tool description review:
  - Action-oriented name:
  - Use this when:
  - Do not use when:
  - Similar-tool disambiguation:
  - Parameter descriptions/enums:
- Tool hints:
  - readOnlyHint:
  - destructiveHint:
  - openWorldHint:

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
- Deny write actions whose JSON payload has not been reviewed for target, scope, sensitive fields and side effects.
- Deny unbounded selectors and bulk writes without affected_count, max limit, dry-run summary and explicit approval.
- Deny credential reads without owner and purpose.
- Deny non-allowlisted provider/base URL when tools are enabled.
- Deny treating conversation-local remembered approvals as reusable profile policy.
- Deny read-only classification when a tool mutates state, sends data externally, triggers jobs, or logs sensitive query content.

## Guard Tests

| Case | Input | Expected decision | Evidence |
|---|---|---|---|
| allow-path |  | allow |  |
| deny-path |  | deny |  |
| deny-scope |  | deny |  |
| deny-unbounded-bulk |  | deny |  |
| deny-unreviewed-json-payload |  | deny |  |
| postcondition-failure |  | deny |  |

## Data-only MCP Shape

- Implements `search`: yes/no
- Implements `fetch`: yes/no
- `search` returns `structuredContent.results[].id/title/url`: yes/no
- `fetch` returns `structuredContent.id/title/text/url`: yes/no
- Prompt-injection review:
- Citation URL policy:
- Raw text retention policy:

## Rollback

- Disable step:
- Config restore point:
- Verification command:
