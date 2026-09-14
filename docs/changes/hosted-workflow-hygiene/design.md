# Design: hosted-workflow-hygiene

## Decision
Apply a narrow hosted-CI hygiene layer without changing product workflow topology or release evidence semantics.

## Read-only workflow policy
For `platform-vnext`, `codex-consumer-contract`, and `digital-worker-contract`:

```yaml
permissions:
  contents: read
concurrency:
  group: <workflow>-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

Each checkout sets `persist-credentials: false`.

## Evidence-preserving exception
Codex and Digital Worker consumer contracts intentionally retain full history and tags. They validate the fixed `v5.1.0` historical release baseline and therefore must keep:

```yaml
fetch-depth: 0
fetch-tags: true
```

## Safety boundary
- PR supersession may cancel obsolete read-only runs.
- Main push and manual dispatch runs use unique `run_id`, so fresh-main evidence is not cancelled by later events.
- Branch-GC remains `cancel-in-progress: false` because it has cleanup/apply semantics.

## Verification
`tests/test_hosted_workflow_hygiene.sh` statically enforces the above invariants and is invoked from the existing quick/full workflow contract test.

## Rollback
Revert this isolated change. No product manifest or runtime state migration is involved.
