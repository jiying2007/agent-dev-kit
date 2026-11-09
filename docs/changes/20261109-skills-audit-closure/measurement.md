# Exact source-byte footprint — not runtime token measurements

Computed from Git trees baseline=a16df58ba717e2de6d8ab70847a6aa11281debd8, candidate=caabc758c3e2813db7242bd610da35533b0ccdbf with profile inheritance and skills/agents plus asset-local support files. All baseline computed values exactly matched existing ratchets.

| Profile | Entry before | Entry after | Δ | Full before | Full after | Δ |
|---|---:|---:|---:|---:|---:|---:|
| core | 133143 | 133576 | 433 | 177749 | 180984 | 3235 |
| release-hardening | 110205 | 110194 | -11 | 148781 | 151572 | 2791 |
| personal-core | 152125 | 152554 | 429 | 197913 | 201144 | 3231 |
| embedded-fullstack | 235950 | 237905 | 1955 | 290959 | 295716 | 4757 |
| team-core | 165420 | 166078 | 658 | 216369 | 220184 | 3815 |
| large-refactor | 238982 | 240937 | 1955 | 297297 | 302190 | 4893 |
| incident-response | 36410 | 36395 | -15 | 40973 | 40958 | -15 |
| research-intake | 85412 | 85973 | 561 | 123384 | 123945 | 561 |

Increases reflect reviewed delivery and safety fixes, especially AAR portable support, and must not be interpreted as actual model prompt loading or token savings. Where measured bytes decreased, the tightened threshold is preserved.
