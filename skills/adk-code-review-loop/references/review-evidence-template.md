# Code Review Evidence Template

## Snapshot commands

```bash
rtk git rev-parse HEAD
rtk git status --short
rtk git diff --check
rtk git diff --cached
rtk git diff --check --cached
<project-lint-cmd> && <project-test-cmd>
```

## Full report

```md
- Review Scope:
- Review Target: staged | working-tree | whole-branch
- Snapshot ID:
  - head:
  - index_or_diff:
- Working Tree Overlay:
  - target_paths_with_unstaged_changes:
  - latest_worktree_reviewed: true | false
- Reviewer Independence: independent | author-self-review
- Review Round:
- Review Mode: targeted-finding-review | whole-diff-review | whole-lifecycle-review
- Finding Classes:
- New Finding Class Count:
- Reopened Finding Count:
- Consecutive Clean Reviews:
- Requirement Baseline:
- Domain Model Baseline:
- Verification Baseline:
- Lifecycle Operation Baseline: not_applicable | <path + digest>
- Contract Change Decision: none | design-change
- Replan Reason:
- Mechanical Gate: pass | fail | not-run
- Spec Verdict:
- Quality Verdict:
- Semantic Review: no-finding | findings-open | needs-context
- Findings:
  | ID | Severity | File | Evidence | Required Action | Status |
  |---|---|---|---|---|---|
- Cannot Verify From Diff:
- Spec-to-Code Ledger (when applicable): requirement->code / code->spec / not-checked / owner-risk-decision
- False Positives:
- Out-of-scope Suggestions:
- Review Coverage Ledger (whole-diff/whole-lifecycle when applicable):
  | Scope ID | Source Snapshot | Inspected/Uninspected/Unavailable | Evidence | Owner/Risk Decision |
  |---|---|---|---|---|
- Patch Validation (when applicable): base / patched / original_repro / related_variants / legitimate_behavior / new_risks / not-tested
- CI/PR Review Boundary:
  - trusted_trigger:
  - protected_secret_exposure:
  - structured_output_valid:
  - inline_anchor_valid:
- Fix Plan:
- Re-review Result:
- Final Verdict: pass | needs-fix
- Quality Verdict: locally-clean | independent-final-pass | needs-fix
- Final Readiness: true | false
```
