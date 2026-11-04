# Skill capability convergence — requirements

## Goal
Make ADK Skill routing capability-based, not language-siloed. Remove redundant legacy content and protect read-only authorization while preserving Chinese output and non-Chinese portability.

## Non-goals
No new LLM runtime, no real model campaign, no device flashing, no direct write to Codex/Claude/OpenCode live homes, no use of Codex or ChatGPT Work shared quota.

## Acceptance
1. Manifest and Profile contain 56 core + 8 optional Skills, with no shipped `adk-chinese-*` aliases.
2. Unified `adk-code-review-loop` handles Chinese/English requests, preserving blocker/major semantics and real review evidence.
3. Commit quality gate uses repo locale and has read-only deterministic syntax checker; no implicit `git commit`, `--amend`, `push`, `merge`.
4. All extant `skills/*/agents/openai.yaml` have `interface` mapping; old `references/details.md` files no longer clone Skill frontmatter or Workflow.
5. Remove obsolete minimum-line/fixed-heading tests; new tests verify identity, descriptions, scope, v2 behavior and negative/abstain routing.
6. Version strictly advances to 10.0.0 before PR; release and Root promotion remain independent protected steps.

## Required evidence
Fresh Python 3.11 and 3.12 contract + regression CI, diff/format checks, source-bound review, immutable tag/release and verified downstream lock/source-to-live promotion if/when executed.

## Blocker policy
Any contract mismatch, untrusted SCM side effect, missing required CI, or unreconciled downstream pin blocks release/consumer claims, but not independent source-only refinement.
