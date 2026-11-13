# Completion Skill entry progressive disclosure

Baseline: `adk-verification-before-completion/SKILL.md` was **9476 UTF-8 bytes**, close to the 9500-byte bound; it unconditionally included a large final report template despite a declared checkpoint/final distinction.

Change: keep one Skill and one authority. Use stage (checkpoint vs goal-final) × risk (low/medium/high). A minimal entry retains fail-closed applicability, source freshness, independence and completion guard. Move the original full Evidence Template into the existing `references/verification-governance-details.md` without deleting field semantics. This cuts the entry's source byte surface to **6705 bytes** (source-only observation, not a measured runtime-token saving).

Add 9 descriptive scenario expectations and deterministic content tests via existing `tests/test_skill_content.sh`. Do not claim real behavior improvement or change machine permission/routing. The normal 102-suite CI, independent review and exact-version release gates remain mandatory.
