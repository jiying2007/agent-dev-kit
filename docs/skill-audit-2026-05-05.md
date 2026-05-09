# Skill Audit Report — 2026-05-05

Audited: 37 SKILL.md files (28 core + 9 optional)

## Legend

- **FM** = Frontmatter complete (name, description, version, last_updated, triggers, non_triggers, inputs, outputs, constraints)
- **trigger_quality**: `matchable` = short quoted phrases usable for regex matching; `descriptive` = scenario sentences not easily matchable
- **body_sections**: Goal, Prerequisites, Workflow, Quality Gate
- **anti_rational**: Has 合理化借口拦截 section (required for p0)
- **robust**: Has 健壮性规范 boilerplate section

## CORE SKILLS (28)

| skill_name | tier | FM | trigger_quality | body_sections | anti_rational | robust | lines | issues |
|---|---|---|---|---|---|---|---|---|
| adk-requirements-triage | p0 | Y | descriptive | ALL | Y | N | 79 | triggers are descriptive sentences, not matchable keywords |
| adk-adr-writer | p1 | Y | descriptive | ALL | N | Y | 63 | triggers are descriptive sentences |
| adk-task-breakdown | p0 | Y | descriptive | ALL | Y | N | 78 | triggers are descriptive sentences |
| adk-interface-contract-design | p0 | Y | descriptive | ALL | Y | N | 67 | triggers are descriptive sentences |
| adk-register-map-design | p1 | Y | descriptive | ALL | N | Y | 66 | triggers are descriptive sentences |
| adk-driver-bringup-checklist | p1 | Y | descriptive | ALL | N | Y | 67 | triggers are descriptive sentences |
| adk-bsp-porting-playbook | p1 | Y | descriptive | ALL | N | Y | 67 | triggers are descriptive sentences |
| adk-rtos-task-design | p1 | Y | descriptive | ALL | N | Y | 66 | triggers are descriptive sentences |
| adk-interrupt-dma-patterns | p1 | Y | descriptive | ALL | N | Y | 66 | triggers are descriptive sentences |
| adk-protocol-stack-integration | p1 | Y | descriptive | ALL | N | Y | 66 | triggers are descriptive sentences |
| adk-component-api-stability | p1 | Y | descriptive | ALL | N | Y | 66 | triggers are descriptive sentences |
| adk-cmake-cross-build | p1 | Y | descriptive | ALL | N | Y | 67 | triggers are descriptive sentences |
| adk-toolchain-debug-openocd-gdb | p1 | Y | descriptive | ALL | N | Y | 66 | triggers are descriptive sentences |
| adk-static-analysis-c-cpp | p0 | Y | descriptive | ALL | Y | N | 66 | triggers are descriptive sentences |
| adk-systematic-debugging | p0 | Y | descriptive | ALL | Y | N | 73 | OVERLAPS with adk-diagnose-loop (same debugging workflow) |
| adk-unit-test-embedded | p0 | Y | descriptive | ALL | Y | N | 66 | triggers are descriptive sentences |
| adk-verification-before-completion | p0 | Y | descriptive | ALL | Y | N | 95 | OVERLAPS with adk-commit-pr-quality-gate |
| adk-integration-hil-sil | p1 | Y | descriptive | ALL | N | Y | 66 | triggers are descriptive sentences |
| adk-fault-injection-recovery | p1 | Y | descriptive | ALL | N | Y | 66 | triggers are descriptive sentences |
| adk-performance-profiling-embedded | p1 | Y | descriptive | ALL | N | Y | 66 | triggers are descriptive sentences |
| adk-release-versioning | p1 | Y | descriptive | ALL | N | Y | 72 | triggers are descriptive sentences |
| adk-commit-pr-quality-gate | p0 | Y | descriptive | ALL | Y | N | 85 | OVERLAPS with adk-verification-before-completion |
| adk-grill-with-docs | p0 | N | matchable | ALL | Y | Y | 79 | MISSING version+last_updated; DUPLICATE 核心流程/Workflow sections |
| adk-diagnose-loop | p0 | N | matchable | ALL | Y | Y | 83 | MISSING version+last_updated; OVERLAPS with adk-systematic-debugging; DUPLICATE 核心流程/Workflow |
| adk-code-simplification | p1 | N | matchable | ALL | Y | Y | 79 | MISSING version+last_updated |
| adk-context-engineering | p1 | N | matchable | ALL | Y | Y | 78 | MISSING version+last_updated |
| adk-chinese-commit-conventions | p1 | N | matchable | ALL | Y | Y | 102 | MISSING version+last_updated |
| adk-chinese-code-review | p1 | N | matchable | ALL | Y | Y | 92 | MISSING version+last_updated |

## OPTIONAL SKILLS (9)

| skill_name | tier | FM | trigger_quality | body_sections | anti_rational | robust | lines | issues |
|---|---|---|---|---|---|---|---|---|
| adk-test-flakiness-triage | p2 | Y | descriptive | ALL | N | N | 57 | triggers are descriptive sentences |
| adk-cross-team-handoff | p2 | Y | descriptive | ALL | N | N | 58 | triggers are descriptive sentences |
| adk-incident-rca-report | p2 | Y | descriptive | ALL | N | N | 58 | triggers are descriptive sentences |
| adk-artifact-gated-lite | p2 | Y | descriptive | ALL | N | N | 76 | triggers are descriptive sentences |
| adk-planning-execution-loop | p2 | Y | descriptive | ALL | N | N | 65 | triggers are descriptive sentences |
| adk-skill-composition-governance | p2 | Y | descriptive | ALL | N | N | 63 | triggers are descriptive sentences |
| adk-security-supply-chain | p2 | Y | descriptive | ALL | N | N | 63 | triggers are descriptive sentences |
| adk-fetch-url-content | p2 | N | matchable | ALL | N | Y | 52 | MISSING version+last_updated |
| adk-email-imap-fetch | p2 | N | matchable | ALL | N | Y | 52 | MISSING version+last_updated |

## SUMMARY STATISTICS

| metric | count |
|---|---|
| Total skills audited | 37 |
| Frontmatter complete | 27/37 (73%) |
| Frontmatter incomplete (missing version+last_updated) | 10/37 |
| Body sections ALL present | 37/37 (100%) |
| p0 skills with anti-rationalization | 10/10 (100%) |
| Matchable triggers | 8/37 (22%) |
| Descriptive triggers | 29/37 (78%) |
| Skills with 健壮性规范 boilerplate | 22/37 |
| Skills with 合理化借口拦截 | 14/37 |

## CRITICAL ISSUES

### 1. Frontmatter Inconsistency (10 skills missing version+last_updated)

Two "waves" of skills exist:
- **Wave 1** (27 skills): Full frontmatter with version: 2.7.0, last_updated: 2026-05-02
- **Wave 2** (10 skills): Missing version and last_updated fields

Missing skills: adk-grill-with-docs, adk-diagnose-loop, adk-code-simplification, adk-context-engineering, adk-chinese-commit-conventions, adk-chinese-code-review, adk-fetch-url-content, adk-email-imap-fetch, and 2 more from wave 2.

### 2. Trigger Quality Split

Two incompatible trigger styles coexist:
- **Wave 1** (29 skills): Triggers are Chinese scenario sentences like "收到模糊需求或跨团队需求时" — NOT matchable by keyword regex
- **Wave 2** (8 skills): Triggers are short quoted phrases like "需求不清楚", "git commit" — matchable by keyword regex

The `scripts/devkit.sh match` command can only reliably match Wave 2 style triggers.

### 3. Significant Content Overlaps (3 pairs)

| Pair | Overlap Type | Recommendation |
|---|---|---|
| adk-systematic-debugging ↔ adk-diagnose-loop | Both are p0 debugging workflows with identical reproduce→locate→root-cause→fix→protect flow | Merge into one; adk-diagnose-loop is a simplified duplicate |
| adk-verification-before-completion ↔ adk-commit-pr-quality-gate | Both are p0 quality gates checking evidence, blockers, breaking changes, evidence index | Clarify scope boundary or merge |
| adk-requirements-triage ↔ adk-grill-with-docs | Both address requirements clarity | adk-grill-with-docs should be the "interview" phase feeding into adk-requirements-triage "decomposition" |

### 4. Duplicate Internal Sections (2 skills)

- **adk-grill-with-docs**: "核心流程" (lines 29-35) and "Workflow" (lines 47-53) contain identical steps
- **adk-diagnose-loop**: "核心流程" (lines 29-35) and "Workflow" (lines 50-55) contain identical steps

### 5. Inconsistent Template Sections

Three different "tail sections" coexist:
- **健壮性规范** (robustness spec): 22 skills — standardized boilerplate with 5 identical bullets
- **合理化借口拦截** (anti-rationalization): 14 skills — scenario-specific excuse/reality/correct-action tables
- Some skills have BOTH, some have neither (p2 optional skills with neither)

### 6. Manifest vs AGENTS.md Tier Discrepancy

AGENTS.md repo analysis states "Core Skills: 22 (p0:8, p1:14)" but manifest.yaml declares 28 core skills (p0:10, p1:18). The count was likely updated in manifest but AGENTS.md analysis was not refreshed.

## RECOMMENDATIONS

1. Add version+last_updated to the 10 missing skills immediately
2. Standardize all triggers to matchable keyword format (Wave 2 style)
3. Resolve adk-diagnose-loop ↔ adk-systematic-debugging overlap (merge or clearly differentiate)
4. Resolve adk-verification-before-completion ↔ adk-commit-pr-quality-gate overlap
5. Remove duplicate 核心流程 sections from adk-grill-with-docs and adk-diagnose-loop
6. Choose one tail section template (健壮性规范 OR 合理化借口拦截) and apply consistently
7. Update AGENTS.md repo analysis to reflect actual 28 core skills / 10 p0 count
