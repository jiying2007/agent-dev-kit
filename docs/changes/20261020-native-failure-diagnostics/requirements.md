# Native campaign failure diagnostics requirements

This change addresses one observed source defect: a failed hosted Native campaign loses its bounded diagnostic evidence because the remaining packaging and upload steps require success.

| Requirement | Acceptance |
|---|---|
| REQ-001 | ACC-001: After trusted checkout, Python setup and runtime installation succeed, a later failure can retain the last successful workflow phase, failed phase, explicit not-run phases and available validated campaign observations. The original failed step and job remain failed. |
| REQ-002 | ACC-002: A new private output directory contains only one bounded metadata JSON. Only six fixed campaign JSON filenames may be inspected. Symlink paths, non-regular files, oversized input, ambiguous JSON and unknown schema fields are rejected without copying raw content. |
| REQ-003 | ACC-003: Diagnostics never create or upload a receipt, signature, registry or target contract and never confer qualification or release authority. The successful candidate pipeline retains its existing gates. |

The collector is an internal hosted-workflow utility, not a new Native qualification API. It requires no provider invocation, paid model, network access or new dependency. Python 3.8 package compatibility remains required.
