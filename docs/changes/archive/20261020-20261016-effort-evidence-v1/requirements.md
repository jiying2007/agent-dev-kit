# Requirements

REQ-001: Route-derived E0–E3 advisory level must be deterministic, risk-conservative, not an authorization change.
REQ-002: Unknown risk does not gain E1; release/high-risk/live-device/Flash/storage escalation cannot be downgraded.
REQ-003: Maintain the R2 canonical requirements/design/tasks files while minimizing E1 content only when explicitly approved.
REQ-004: Add bounded falsification and alternating reproducible performance evidence to existing Skills; no universal additional Agent calls.
Acceptance: deterministic Python 3.8/3.11/3.12 regression and exact-head CI.
Non-goals: automatic E1 for unknown risk, measured Token/task-performance gains, equipment flash, third-party plugin installs.
