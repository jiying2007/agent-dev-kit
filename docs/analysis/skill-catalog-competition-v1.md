# Skill Catalog 竞争评估 v1

Status: source-candidate / deterministic-only
Baseline: ADK 8.0.18 @ `2fe242e9e309e4111c8639e511e53f6a585a1ed7`
Candidate: ADK 8.0.19 (以最终 PR exact-head 为准)

## Decision

借鉴 Addy Osmani 的 skill activation/catalog-level eval 方法，只增强 ADK 原生 `match_text()` 评估入口；不引入 Addy/Matt/pstack 的 Skill 文件、模型依赖、安装脚本、额外路由器或生命周期。

## Evidence boundary

- Existing single-Skill trigger matrix: `tests/fixtures/skill_trigger_cases.tsv`.
- New whole-catalog competition replay: `tests/fixtures/skill_catalog_competition.tsv`.
- Both run through `tests/test_skill_trigger_matrix.py` and existing `tests/test_skill_trigger_matrix.sh`, hence the established CI regression list.
- A collision case explicitly proves the losing Skill also matches *when named*, but the only authoritative implicit decision is the production matcher winner.
- Negation cases reject a named Skill and require global abstention; unknown requests must fail closed with denied mutation.
- Corpus is a hand-reviewed deterministic fixture, not a measured production request distribution. No rank probability, LLM success rate, runtime Token reduction, or field performance has been established.

## Admission and removal

Future routing/description changes must not regress the selected winner, abstention or competitor signal without a separately reviewed fixture change; source SHA and test outcome are the evidence identity. Add representative consented real wording only after sanitization and labeling. Compare source-fixed A/B/C behavior under the same model and budget before claiming an agent-level improvement. If no measurable quality benefit emerges, retain the small regression suite but do not expand orchestration or add Skill assets.

Upstream sources are *method-only* reference evidence: `addyosmani/agent-skills@aeac41d4`, `mattpocock/skills@49dd158d`, `cursor/plugins@f713f142`. No upstream source copied or executed. Source, license and independent acceptance remain governed by Root `docs/absorption-governance.md`.
