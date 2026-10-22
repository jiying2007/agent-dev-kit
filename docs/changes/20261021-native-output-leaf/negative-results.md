# Negative results

The independent original CLI reproduction accepted a symbolic-link `--plan-out` outside the repository for both an existing and a nonexistent target. Each invocation returned exit 0 and status `ready`. The fixture target was overwritten or created and the sibling candidate output was generated. Raw stdout, stderr and terminal process receipts are retained in the session audit under `oct21-continue-native/original-cli-reproduction/`.

The test uses only the prepare stage and an owned fixture. It is not authenticated native discovery/load/trigger evidence and does not satisfy ADK #153.

Before the fix, the newly added acceptance regressions ran as three test methods: the ordinary external regular-file control passed; four `prepare` combinations (plan/candidate output and existing/dangling target) failed because the command incorrectly succeeded; two `run` subcases failed because the execution spy was called before output rejection. This was exit 1 with six assertion failures. Raw streams and the terminal receipt are preserved under `oct21-continue-native-implementation/red-tests/` rather than replaced by the later passing result.
