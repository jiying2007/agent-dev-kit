# Native campaign project-layout correctness requirements

1. A real native campaign must place rendered skills on the target runtime's reviewed project-level discovery path, not merely in an arbitrary temporary skills directory.
2. Claude Code campaign skills must resolve under project `.claude/skills/`; OpenCode campaign skills must resolve under project `.opencode/skills/`.
3. Stage commands must run with the isolated project root as cwd.
4. `ADK_TARGET_ROOT` must identify the project config root and `ADK_TARGET_PROJECT_ROOT` the project root.
5. `auth_mode=home` must preserve HOME authentication separately; the campaign must not redirect Claude's user config/credential root to the temporary project bundle.
6. Target-layout metadata must be reviewed, freshness-bounded, safe-relative, and cover every direct target.
7. Existing campaign plan/evidence/receipt v1 schemas and authority semantics remain unchanged.
8. This correctness-only behavior change advances the source patch version to 7.4.1.
