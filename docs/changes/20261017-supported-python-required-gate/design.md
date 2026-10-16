# Design

The canonical .github/workflows/ci.yml already runs contract and regression jobs as 3.8/3.11/3.12 matrices. Native ruleset 23394761 requires deterministic-eval-package, but not the 3.8 matrix legs directly.

Reuse this required check as an aggregate gate: add needs [contract, regression] with always(); its first step fails unless both full matrices return success. Do not change native ruleset identity or create an alternate ruleset authority. This trades package-job parallelism for strictly enforced 3.8 merge safety. It does not run duplicate Python 3.8 tests.

tests/test_hosted_workflow_hygiene.sh protects the aggregate DAG and mutates each critical condition to prove fail-closed behavior. Rollback: revert the exact PR and restore source version identity; any failed or skipped required check blocks merging.
