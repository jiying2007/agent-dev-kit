# 7.3.0 native candidate campaign requirements

1. Execute discovery/load/trigger as three independent caller-approved commands with no shell interpolation.
2. Bind the candidate receipt to exact runtime binary SHA-256, exact version pin, target/profile bundle digest and prospective normalized contract digest.
3. Bound each stage by timeout and stdout/stderr byte budgets; discard raw output after hashing.
4. Require all stages to exit zero and have independent command/result digests.
5. Emit the existing strict native conformance receipt schema, not a parallel evidence format.
6. Never modify the target contract, live runtime directories or product qualification.
7. Candidate success must remain not-certified, promotion-ineligible and without lifecycle authority until a managed external trust verifier validates provenance.
8. Enter quick/full regression and advance SemVer because this adds a public target CLI capability.
