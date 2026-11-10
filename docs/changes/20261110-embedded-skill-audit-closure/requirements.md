# Embedded Skills audit closure — requirements

- Baseline ADK 11.2.1 main a5ba89065b163594571cc673dd436a23524725a6; candidate 11.2.2.
- Fix routing migration/build over-trigger and HardFault/FromISR/DNS under-trigger; fix timeout/retry, Linux-vs-MCU IRQ, MC/DC, CTest/HIL example, Scapy Bash syntax, and static analysis gates.
- Add five embedded-only deferred references. Do not duplicate an existing Skill/Profile or add external executable code.
- No Codex/Work shared quota, no private repo, no paid model experiments, no unapproved live-device writes.
- Accept only exact regression tests + strict/full CI + zero-padded Profile source ratchets; native runtime and field qualification remain separate.
