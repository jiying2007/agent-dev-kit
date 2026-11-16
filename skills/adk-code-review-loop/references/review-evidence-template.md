# Code Review Evidence Template

## Snapshot commands

先设置 `review_target`。whole-branch 的 `review_base` 须来自已核验的审查基线，不猜默认分支。working-tree 指 HEAD 到当前已跟踪文件的净差异（含 staged+unstaged），不包含 untracked 正文；按 scope 读取或记录排除项，不为取证改 index。

```bash
set -euo pipefail
review_head=$(git rev-parse HEAD)
printf '%s\n' "$review_head"
git --no-optional-locks status --short --untracked-files=all
case "${review_target:?set staged, working-tree or whole-branch}" in
  staged) review_diff=(--cached "$review_head") ;;
  working-tree) review_diff=("$review_head") ;;
  whole-branch)
    review_base=$(git rev-parse --verify --end-of-options "${review_base:?set verified baseline}^{commit}")
    review_start=$(git merge-base "$review_base" "$review_head")
    printf 'base %s merge-base %s\n' "$review_base" "$review_start"
    review_diff=("$review_start" "$review_head") ;;
  *) exit 2 ;;
esac
git -c diff.autoRefreshIndex=false diff "${review_diff[@]}"
git -c diff.autoRefreshIndex=false diff --check "${review_diff[@]}"
<project-lint-cmd> && <project-test-cmd>
```

whole-branch 只含 merge-base 到 HEAD；status 中 dirty/untracked 为独立 overlay，未另审时 `latest_worktree_reviewed: false`。记录 base、merge-base、head 及实际 diff 身份；文件变化后重新取证。

## Full report

```md
- Review Scope:
- Review Target: staged | working-tree | whole-branch
- Snapshot ID:
  - head:
  - base / merge-base: <whole-branch only>
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
- Review Independence Result: locally-clean | independent-final-pass | needs-fix
- Final Readiness: true | false
```
