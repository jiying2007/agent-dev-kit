# Native campaign full-process deadline — requirements

- A native campaign invocation must bound wall time through process exit **and** complete stdout/stderr drains; an exited launcher with inherited pipe handles must not bypass `timeout_seconds`.
- Timeout, shared-output-byte-budget and caller cancellation must stop the POSIX session/process group and cancel all outstanding readers.
- Keep the existing command, environment, privacy, receipt and target identity contracts unchanged. Never promote a synthetic test to real native G21 evidence.
- Preserve supported Python 3.8+ syntax and a bounded negative regression that fails on the former launcher-exit/drain gap.
