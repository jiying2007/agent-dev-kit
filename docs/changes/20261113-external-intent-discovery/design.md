# External Skills / Prompt discovery — design

Baseline: ADK 11.2.12 refined two intake Skills but retained legacy-only trigger phrases. Ordinary expressions like “全网搜索优质skills，参考优化ADK skills” and “逆向 Prompt 调用链” had no corresponding exact trigger. This is a source discovery gap, not evidence of host model failure.

Decision: add a few specific phrases to the existing `adk-skill-deep-analysis` and `adk-repo-prompt-analysis` frontmatter. Keep original descriptions, non-triggers, permissions, Manifest intents and fallback authority unchanged. Distinguish method-only research from the existing explicit `吸收外部实践` workflow.

Verification: `tests/fixtures/skill_trigger_cases.tsv` adds nine direct positive/negative cases; `skill_catalog_competition.tsv` adds four whole-catalog primary and negated cases. They run in the existing `tests/test_skill_trigger_matrix.py` production matcher, not a mock. Strict, full and security CI remain mandatory. No new Skill, Agent, Workflow, scheduled task, private repo or paid Codex/Work API call.
