# 11.2.0 Method Quality — Profile source byte accounting

All numbers below count actual UTF-8 Git blob sizes of registered Agent/Skill entry files and their `references/scripts/assets` on the exact source tree, not native runtime prompt or token measurements.

| Profile | Previous actual entry/full | Candidate actual entry/full | Delta entry/full |
|---|---:|---:|---:|
| core | 131312 / 169046 | 133143 / 177749 | +1831 / +8703 |
| release-hardening | 108494 / 140198 | 110205 / 148781 | +1711 / +8583 |
| personal-core | 150294 / 189210 | 152125 / 197913 | +1831 / +8703 |
| embedded-fullstack | 234119 / 282256 | 235950 / 290959 | +1831 / +8703 |
| team-core | 163471 / 207548 | 165420 / 216369 | +1949 / +8821 |
| large-refactor | 236544 / 286712 | 238982 / 297297 | +2438 / +10585 |
| incident-response | 36070 / 39371 | 36410 / 40973 | +340 / +1602 |
| research-intake | 84358 / 117687 | 85412 / 123384 | +1054 / +5697 |

Source commits: ADK 11.1.0 `0160d9cdfc00b723678cd52eb5e51cf9e14f31cb` tree `f55293dec57c0dd7cfc65372f29044ffe0b73ab9`; method candidate `f62fa5bd5fd6c4052f8c2a40cfc588fdf5a6c7c6` tree `2af49544f53e501d7782d89aefec4a1a219a1a2a`.

The previous ratchet baseline had unused headroom; the new limits use candidate **actual** measurements, with no slack. Full surface contains newly added on-demand references and is **not** evidence that every prompt loads these bytes. Source-only content growth is justified by concrete new diagnostic, TDD, architecture, skill-behavior and prototyping procedures, all conditioned on task relevance. No host tokenizer or native model experiments were run; effect quality remains `not-measured`.

To verify: `python -m unittest tests.test_profile_context_footprint -v` plus `bash tests/test_profile_context_footprint.sh` if present. No risk/authorization gates are relaxed.
