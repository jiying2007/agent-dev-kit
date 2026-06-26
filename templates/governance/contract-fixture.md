# Contract Fixture Template

fixture_id:
schema_version:
description:
runtime_enabled: false
fixture_mode: method-only

## Source Mapping

source_mapping:
  source_report:
  source_ids:
    -
  adopted_as:
  rejected_runtime_surface:
    -
  clean_room_statement:

## Contract Under Test

contract_under_test:
  id:
  purpose:
  required_fields:
    -
  oracle_or_assertion:
  verification_command:
  evidence_path:
  rollback_path:

## Positive Fixture

positive_fixture:
  path:
  required_fields_present:
    -
  local_ci_parity:
  artifact_lineage:
    version_or_digest:
    materialization_time:
    retention_policy:
  expected_result: pass

## Negative Fixture

negative_fixture:
  path:
  expected_failure:
  missing_or_invalid_field:
  expected_result: fail

## Evidence

validation:
  commands:
    - command:
      exit_code:
      result_summary:
  negative_or_disproved_path:

## Authoring Rules

- Keep `runtime_enabled: false` unless an owner-approved runtime gate exists.
- Keep `fixture_mode: method-only` for external practice absorption.
- Use clean-room content; do not copy upstream task data, runtime code, secrets or benchmark assets.
- Every promoted contract fixture needs at least one positive example and one negative example.
- Positive fixtures must include an oracle or deterministic assertion.
- Pipeline claims must include local CI parity.
- Artifact claims must include version or digest lineage.
- Negative fixtures must fail for the expected gate reason.
- Record rollback path and source mapping before promotion.
