# Required negative results

The patch must fail closed when:

- the target-layout manifest is missing, unsafe, oversized, stale or does not cover every direct target;
- a project config directory is absolute, traversing, multi-segment or contains control characters;
- a target's discovery scope is not project-local;
- stage cwd differs from the isolated project root;
- the rendered `skills/` tree is absent beneath the reviewed project config root.

A campaign that runs from a generic temporary `skills/` root must not be treated as native discovery evidence.
