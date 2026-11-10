# Exact source bytes — 11.2.2 candidate

Computed from source tree at cfe82bf7086b11aa8c7e41822bca624951a535d9, using manifest Profile inheritance plus source entry files and references/scripts/assets. No additional slack. These measurements are not tokenizer output or runtime initial context size.

| Profile | Assets | Entry before | Entry after | Delta | Full before | Full after | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| core | 27 | 133576 | 133940 | +364 | 180976 | 184133 | +3157 |
| release-hardening | 23 | 110194 | 112256 | +2062 | 151564 | 159576 | +8012 |
| personal-core | 32 | 152554 | 152918 | +364 | 201136 | 204293 | +3157 |
| embedded-fullstack | 54 | 237905 | 241585 | +3680 | 295708 | 309519 | +13811 |
| team-core | 35 | 166078 | 166442 | +364 | 220176 | 223333 | +3157 |
| large-refactor | 55 | 240937 | 244617 | +3680 | 302182 | 315993 | +13811 |
| incident-response | 9 | 36395 | 37797 | +1402 | 40958 | 46612 | +5654 |
| research-intake | 20 | 85973 | 86571 | +598 | 123945 | 124543 | +598 |

Increased deferred bytes reflect new task-specific reference materials, not default prompt consumption. Benchmark only with the same native runtime/model/task and independent scoring.
