---
id: global-engineering-rules
title: Global Engineering Rules
languages: [all]
layers: [all]
stages: [design, build, review]
checks: [design-rules-documented]
---

# Global Engineering Rules

These rules apply across all languages and stacks in this repository unless a more specific rule overrides them.

## Core Principles

- Optimize for readability, correctness, and safe change over cleverness.
- Make the smallest change that fully solves the problem.
- Prefer explicit code over magical or highly implicit behavior.
- Keep modules cohesive and responsibilities narrow.
- Do not introduce a new abstraction until duplication or volatility justifies it.

## Change Boundaries

- Do not change public contracts, storage formats, or externally visible behavior without updating docs and migration notes.
- Do not mix unrelated refactors with feature work or bug fixes.
- Preserve backward compatibility by default.
- Prefer additive changes before destructive changes.

## Naming And Structure

- Use names that describe business meaning, not temporary implementation detail.
- Keep files and directories predictable and aligned with domain boundaries.
- Avoid generic utility dumping grounds such as `misc`, `helpers`, or `common` unless they have a clear contract.
- Move shared logic into well-named modules only after a real second use appears.

## Functions And APIs

- Keep functions focused on one job.
- Pass explicit inputs and return explicit outputs.
- Avoid hidden mutation of shared state.
- Validate inputs at system boundaries.
- Fail early on invalid state instead of silently continuing.

## Errors And Observability

- Never swallow errors without a deliberate and documented reason.
- Prefer structured error values over string-only errors.
- Log enough context to reproduce and diagnose the issue later.
- Make error messages describe what happened, what was expected, and what the user can try next.

## Testing And Verification

- Treat tests as executable specifications, not just coverage artifacts.
- Prefer deterministic tests over timing-dependent or environment-dependent tests.
- Test behavior and contracts, not internal implementation details.
- Add regression tests for every bug that escapes to production or integration.

## Documentation

- Keep docs close to the code they describe.
- Update docs in the same change that changes behavior.
- Prefer examples over abstract explanations.
- Record negative decisions and tradeoffs, not only final choices.

## Security And Safety

- Do not hardcode credentials, tokens, or secrets.
- Validate and sanitize external input at trust boundaries.
- Prefer least-privilege defaults.
- Make dangerous operations explicit and auditable.

## Embedded-Specific Rules

- Never assume heap allocation is safe in ISR context.
- Always check return values from hardware access functions.
- Use volatile for memory-mapped registers.
- Prefer static allocation for safety-critical paths.
- Document timing constraints and interrupt priorities.

## Workflow Rules

- Follow the 8-stage lifecycle: Spark → Design → Tasks → Build → Review → Test → Ship → Reflect.
- Each stage has clear inputs, outputs, and gates.
- Gates only block things that are frequently forgotten and cause high-cost failures.
- State is persisted to `.adk/state.json` for interruption recovery.

## Gate Selection Criteria

Before adding a new gate, answer these 4 questions:

1. Is this 100% mechanizable? → Script it
2. Must this be stable and reproducible? → State machine
3. Is this frequently forgotten, and does forgetting cause high-cost failures? → Gate
4. Can this be handled more naturally by agent runtime, skill prompts, or project artifacts? → Don't gate

**Only create a gate if the first three questions are all "yes".**

## References

- VibeFlow absorption report: `reports/vibeflow-absorption-report-20260512.md`
- Lifecycle documentation: `docs/workflows/lifecycle.md`
- Gate mechanism: `AGENTS.md` (Gate 机制设计原则)
