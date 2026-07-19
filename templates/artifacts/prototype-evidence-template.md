# Prototype Evidence

[artifact:adk-prototype-evidence]
structured_output_schema: adk-prototype-evidence-schema-v1

## Identity

- question:
- base_commit:
- scope:
- artifact_path:
- artifact_sha256:

## Execution Evidence

- runtime_assumptions:
- observed_result:
- decision_supported: true | false
- verification_command:
- verification_exit_code:

## Retention

- retention_decision: keep-final | archive-negative-result | delete-orphan | expire
- expires_at:
- cleanup_owner:
- rollback_anchor:
- active_references_absent: true | false

## Boundaries

- 该工件只支持或反驳设计决策，不替代 production test 或 implementation verification。
- 默认保存为 change/evidence 下的 data-only artifact，不写 `.git/`。
- branch/worktree 仅在显式批准后使用，并必须有 expiry、cleanup owner 与 rollback anchor。
