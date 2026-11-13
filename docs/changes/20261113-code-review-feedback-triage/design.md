# Review feedback triage design

Existing full 18-step review is already available on demand under `skills/adk-code-review-loop/references/review-governance-details.md`. The previous 12-step unconditional entry workflow is replaced with a small intent split: `feedback-triage` (read-only/local, no final verdict), `targeted-finding-review` (fresh snapshot, local only), `whole-diff-review` (full spec/quality plus applicable lifecycle). Negative feedback and missing evidence must not become a pass. Full security and independence gates remain in the Skill and reference.

Check deterministic source cases through `tests/test_skill_content.sh`; protected full CI is separate. No real behavior A/B, runtime loaded-context, quality or billed-token claims: `not-measured`. No new Skill/Agent/Workflow.
