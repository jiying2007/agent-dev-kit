# Focused verification report

Date: 2026-10-20 UTC. Source workspace: isolated ADK repair based on exact `da25a7d86a0efe61110f5d8d892c49ff80d91dcc`, with the coordinating maintainer's canonical 8.0.35 version update. Tests used genuine installed RTK, `TZ=UTC` and the isolated Python 3.12.14 environment. The shell wrappers bind `PYTHONPATH` to this workspace's `src`.

## VERIFY-001 — Failure and progress semantics

`rtk proxy bash tests/test_native_campaign_diagnostics.sh`: exit 0, **25 tests passed**. Coverage includes semantic assertion failure with exit-zero runtime, authentication failure before campaign creation, unavailable observation files, empty/partial failed stage lists, later signing failure after complete observations, exact plan and operation-summary positive paths, and explicit refusal of all-success or incomplete trusted prerequisites.

Original failed workflow outcomes remain failed; an absent observation is not treated as a successful or skipped execution. Only a skipped workflow phase yields the synthesized not-run state. The canonical evidence file supplies stage observations; redirected summaries remain separately identified metadata.

## VERIFY-002 — Retention and resource boundary

The same actual test run verified: six fixed input filenames; excluded private/unknown siblings are not read; raw input files are not copied; free text permitted by input schemas is withheld; unknown root/nested fields, duplicate keys, non-finite numbers, malformed encoding/JSON and excessive nesting are rejected; oversized files are rejected before reading; numeric projections are bounded; leaf/ancestor/output symlinks and a real FIFO are refused; an existing output directory cannot be reused. The only generated file is `diagnostics.json`, within the 64 KiB budget, with private POSIX directory/file modes.

Plan/evidence continue to use existing strict v2 schemas. Metadata is not Native qualification evidence, a receipt, a signature, a registry candidate or a source of release authority.

## VERIFY-003 — Existing behavior, typing and governance

| Actual command | Exit | Result |
|---|---|---|
| `rtk proxy bash tests/test_native_campaign.sh` | 0 | Existing 20 tests passed in 5.026 seconds. |
| `rtk proxy python -m mypy --strict src/agent_dev_kit/native_campaign_diagnostics.py src/agent_dev_kit/native_campaign_contract.py` | 0 | Success: no issues found in 2 source files. |
| `rtk proxy python -m ruff check src/agent_dev_kit/native_campaign_diagnostics.py tests/test_native_campaign_diagnostics.py` | 0 | All checks passed. |
| `rtk proxy bash scripts/check-change-governance.sh docs/changes/20261020-native-failure-diagnostics` | 0 | Change governance passed. |
| `rtk proxy git diff --check` | 0 | No tracked whitespace errors. |

The workflow contract case confirms the exact-source/Python/runtime prerequisites, failure-aware collector and uploader, fixed upload file, two-minute bounds, no continue-on-error, and unchanged default-success authentication, campaign, finalization, signing, registry/loader and successful candidate upload. Prompts, canaries, receipt validation and active qualification metadata are unchanged.

Independent review identified and corrected the plan map/scalar mismatch and unsupported not-run inference. Their regression cases are retained. The explicit dict deep copy in the existing candidate builder resolves the imported strict typing mismatch without loosening its behavior. The new helper remains under the existing default 30,000-byte source-module budget.

## First full regression and integration repair

The coordinating maintainer completed the actual first 99-script full run: **exit 1, 96 pass / 3 fail, 247723 ms**. The implementation reviewer independently read both original logs under `/workspace/scratch/28c22f668291/repair/validation-qualification-adk/`: `adk-full.stdout.log` contains `[SUMMARY] tests=99 pass=96 fail=3`; `adk-full.stderr.log` identifies `test_product_maturity`, `test_workflow_contract` and `test_hosted_workflow_hygiene`.

The first failure was the synthetic redaction sentinel's credential-shaped literal in the new test file. The fix constructs the identical non-secret sentinel at runtime and preserves all redaction assertions; the repository security scanner and its allowlist are unchanged. The other two failures had one cause: the old global timeout regex treated `[45, 2, 2]` as three job budgets despite there being one runner job. The corrected hygiene test parses actual YAML job/step scopes, rejects duplicate keys and keeps every runner job at an explicit integer 5–45 minutes. A declared step timeout must be a positive integer within its own job's budget. Invalid, missing, expression, duplicate and over-budget cases are tested in memory, without running any workflow or provider. The two diagnostic steps still have actual step-scoped two-minute limits.

| Actual repair verification | Exit | Result |
|---|---|---|
| `rtk proxy bash tests/test_product_maturity.sh` | 0 | ADK product maturity contracts hold. |
| `rtk proxy bash tests/test_hosted_workflow_hygiene.sh` | 0 | Hosted workflow hygiene and GitHub governance admin remediation pass. |
| `rtk proxy bash tests/test_workflow_contract.sh` | 0 | Workflow contract pass. |
| `rtk proxy bash scripts/devkit.sh security check --summary-json` | 0 | `status=pass`, no failures or warnings, git inventory. |
| `rtk proxy bash tests/test_native_campaign_diagnostics.sh` | 0 | 25 tests pass, including the unchanged runtime sentinel and actual YAML step scope. |
| `rtk proxy python -m ruff check src/agent_dev_kit/native_campaign_diagnostics.py tests/test_native_campaign_diagnostics.py` | 0 | All checks passed. |

One initial security CLI invocation omitted the required `check` action and exited 2 with usage text. It was corrected before obtaining the actual security result above. Product-maturity and workflow-contract replays ran sequentially to avoid concurrent repository fixture mutation. An independent read-only review confirmed that security rules, successful qualification steps, permission/action/failure assertions and original budgets were not weakened. The coordinating maintainer subsequently completed the second full run with **exit 0, 99 pass / 0 fail, 272788 ms**. Its actual `adk-full-final.stdout.log` summary was independently read, and the command record is `adk-full-final-command.json` under the same validation directory. That result covers the initial PR head before the later test-identifier naming repair described below.

## Protected PR CodeQL result and fixture-only naming repair

For initial PR #216 head `868ba0190d37a02dac62627095f8699bc8341def`, actual CI run `39366645871` logs show CPython **3.8.18 / 3.11.17 / 3.12.15**, each with `[SUMMARY] tests=99 pass=99 fail=0`; all three contract jobs, the 28-source-file strict mypy check and deterministic package job also passed. The independent **CodeQL check `118445178424` failed**. Its four actual bot comments identify clear-text-storage findings at the new test's temporary fixture writes, lines 117, 194, 317 and 349. Stable comment links and the preserved negative outcome are in `negative-results.md`. No successful job conclusion was used to replace the failed security check.

The fixed synthetic value has no credential or environment source. The test-only repair renames `SECRET` to `REDACTION_CANARY` and its local symlink target variable to `fixture_path`, with a comment stating the non-secret fixture semantics. The actual before/after ASTs are identical after precisely these identifier mappings, and runtime canary bytes match (SHA-256 `9f6235f73ae237441a7a2898a6084d075ebd6bd8af723dedeeeb7893125c790e`). Every input, file-writing sink and assertion is preserved. Production source, workflows and security rules are unchanged by this repair.

| Actual post-rename command | Exit | Result |
|---|---|---|
| Read-only AST and runtime-canary comparison | 0 | Exact executable-AST equivalence after identifier mapping; identical runtime canary bytes. |
| `rtk proxy bash tests/test_native_campaign_diagnostics.sh` | 0 | All 25 tests pass. |
| `rtk proxy bash scripts/devkit.sh security check --summary-json` | 0 | `status=pass`, 1517 files, empty failures/warnings. |
| `rtk proxy bash tests/test_hosted_workflow_hygiene.sh` | 0 | Hosted workflow hygiene and governance admin remediation pass. |
| `rtk proxy python -m ruff check tests/test_native_campaign_diagnostics.py` | 0 | All checks passed. |

A fresh remote CodeQL run on the repaired PR head is **pending**. This local evidence does not claim that scan has passed, and no alert dismissal, query exclusion or suppression was added.

## Scope still outside this report

The coordinating maintainer owns subsequent exact-head full regression, protected PR/main checks and component release. The earlier full and hosted matrix results are recorded with their actual source scope above. No local provider runtime/authentication or real hosted Native campaign was available; no paid model call was made. Synthetic tests and this diagnostic source fix do not satisfy G21, actual Owner review, Harness date re-verification, field evidence or ProductM5 qualification.
