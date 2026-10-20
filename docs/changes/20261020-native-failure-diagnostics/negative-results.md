# Negative results

## 已验证的负结果

| Case | Observation | Boundary |
|---|---|---|
| Existing hosted failure path | The run command returns non-zero for failed campaign evidence; all later packaging and upload steps require success. | Source control-flow proof; no real Native campaign was run. |
| Reusing successful packaging after failure | Packaging requires finalized receipt files that early failures do not produce. | A separate metadata projection is necessary; the candidate package cannot be made failure-safe by changing only its condition. |
| Initial test setup used identical commands | The actual first diagnostic test run exited 1 with `native_campaign_stage_commands_must_be_independent`. | Corrected the fixture to independent stage commands and assertions; did not weaken the existing campaign guard. |
| Initial valid-plan projection | The actual second diagnostic test run exited 1: valid plan metadata was rejected because plan command/assertion digests are maps, not scalar digests. | Root projection now selects only fixed scalar identities. The valid-plan positive case passes; full plan schema validation remains. |
| Initial imported strict typing | Focused strict mypy exited 1 on the existing candidate builder's Mapping versus dict return at `native_campaign_contract.py`. | Explicitly copy the source mapping into a dict before the existing deep copy. No type ignore or gate relaxation was added. |
| Missing stage records | Independent review demonstrated that the existing v2 schema accepts empty/partial failed evidence; absence does not establish not-run. | Empty/partial regression cases now retain `evidence-unavailable` for missing stages and never fabricate a skipped execution. |
| First actual full repository regression | 99 scripts completed: 96 pass / 3 fail, exit 1. Product maturity rejected the synthetic sentinel's credential-shaped literal; workflow-contract and hosted-hygiene both miscounted the two step budgets as job budgets. | Assemble the same non-secret sentinel at runtime; retain every redaction assertion. Parse actual YAML scopes, preserving each runner job's 5–45-minute budget and validating each declared step against its own job. No security allowlist, timeout or failure-masking exception was added. |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk proxy sed -n '1,450p' .github/workflows/native-claude-conformance.yml` | 0 | Verified default-success-only packaging and upload from the source tree. | `.github/workflows/native-claude-conformance.yml` | source review | REQ-001 |
| `rtk proxy bash tests/test_native_campaign_diagnostics.sh` initial fixture run | 1 | Existing independent-stage guard rejected identical test commands. | `tests/test_native_campaign_diagnostics.py` | test setup negative | REQ-001 |
| `rtk proxy bash tests/test_native_campaign_diagnostics.sh` initial plan run | 1 | 23 tests ran; valid plan positive case failed due to map/scalar projection mismatch. | `tests/test_native_campaign_diagnostics.py` | deterministic negative | REQ-001 |
| `rtk proxy python -m mypy --strict src/agent_dev_kit/native_campaign_diagnostics.py` initial run | 1 | Exposed imported candidate builder Mapping/dict mismatch. | `src/agent_dev_kit/native_campaign_contract.py` | strict typing | REQ-003 |
| `rtk proxy bash tests/test_native_campaign_diagnostics.sh` final run | 0 | 25 tests passed, including privacy, unsafe input and partial evidence boundaries. | `verify-report.md` | deterministic regression | VERIFY-001 / VERIFY-002 / VERIFY-003 |
| `rtk proxy bash tests/test_native_campaign.sh` | 0 | Existing 20 Native campaign tests passed; no provider was called. | `verify-report.md` | existing regression | VERIFY-003 |
| `rtk proxy python -m mypy --strict src/agent_dev_kit/native_campaign_diagnostics.py src/agent_dev_kit/native_campaign_contract.py` | 0 | No issues in 2 source files. | `verify-report.md` | strict typing | VERIFY-003 |
| `rtk proxy python -m ruff check src/agent_dev_kit/native_campaign_diagnostics.py tests/test_native_campaign_diagnostics.py` | 0 | All checks passed. | `verify-report.md` | static quality | VERIFY-003 |
| `rtk proxy bash scripts/check-change-governance.sh docs/changes/20261020-native-failure-diagnostics` | 0 | Required change structure and canonical contract passed. | `verify-report.md` | source governance | VERIFY-003 |
| `rtk proxy git diff --check` | 0 | No whitespace errors in tracked changes. | `verify-report.md` | source hygiene | VERIFY-003 |
| Coordinator `rtk proxy bash tests/run_all.sh`, first full run | 1 | 99 scripts: 96 pass / 3 fail; 247723 ms. Actual logs independently inspected. | `verify-report.md`, first-full log paths | full repository regression | VERIFY-003 |
| `rtk proxy bash tests/test_product_maturity.sh` after integration repair | 0 | ADK product maturity contracts hold. | `verify-report.md` | original failed gate replay | VERIFY-003 |
| `rtk proxy bash tests/test_hosted_workflow_hygiene.sh` after integration repair | 0 | Hosted workflow hygiene and GitHub governance admin remediation pass. | `verify-report.md` | original failed gate replay | VERIFY-003 |
| `rtk proxy bash tests/test_workflow_contract.sh` after integration repair | 0 | Workflow contract pass. | `verify-report.md` | original failed gate replay | VERIFY-003 |
| `rtk proxy bash scripts/devkit.sh security --summary-json` | 2 | Invocation omitted the required action; CLI usage rejected it. This was not treated as a security result. | `verify-report.md` | command correction | VERIFY-003 |
| `rtk proxy bash scripts/devkit.sh security check --summary-json` | 0 | Actual security result pass, empty failures/warnings, git inventory. | `verify-report.md` | security gate | VERIFY-003 |
| `rtk proxy bash tests/test_native_campaign_diagnostics.sh` after integration repair | 0 | All 25 cases pass, including the actual step-scope timeout assertions. | `verify-report.md` | deterministic regression | VERIFY-001 / VERIFY-002 / VERIFY-003 |

Commands in this change use the genuine installed RTK and isolated Python 3.12.14 environment. Actual Python 3.8/3.11, complete repository CI and hosted Native execution require their real CI/runtime environments; no substitute execution is claimed. Provider and Execution Policy entrypoints were unavailable locally, so those gates are not reported as passed. No original Owner review date or Native target qualification was changed.
