# Native campaign timeout — design

The existing `asyncio.wait_for(process.wait(), timeout)` measured only the launcher exit. Subsequent `await stdout_task` / `await stderr_task` had no deadline; descendants could inherit file descriptors and delay EOF.

Use a single `asyncio.wait_for(asyncio.gather(process.wait(), stdout drain, stderr drain), timeout)`, with all three tasks created before awaiting. On any exception or cancellation, kill the POSIX process group even if the launcher already exited, cancel unfinished tasks, join task exceptions and reap the launcher with a bounded fallback. Keep stdout/stderr one shared byte budget.

A deterministic POSIX negative case spawns a short-lived launcher with a grandchild inheriting both pipes. The grandchild holds them for three seconds while the campaign has a one-second limit. It must time out, not pass after the pipes eventually close. Native conformance and human review remain separate authorities.
