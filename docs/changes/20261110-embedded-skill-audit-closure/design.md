# Embedded Skills audit closure — design

1. Storage routing is based on an explicit layout-change intent, not bare SquashFS/UBIFS nouns. Pure readonly/df 100% enters diagnosis; analysis of layout migration risk can still use the migration Skill without device writes.
2. CMake is selected only when the actual build system is CMake. Buildroot/Autotools/Yocto require source/build metadata triage; Buildroot's CMake packages remain eligible.
3. Use existing Skill routing plus lazy references for MCU fault/wakeup, ISR/DMA, storage/network/display/motor, resource measurement and multi-MCU OTA. No duplicate layer.
4. Protect target identity, explicit authorization, recovery, and postcondition for all live-device state changing effects. Test source and runtime/field evidence must remain distinct.
5. Use project-specific timeout and test runner. Reject phantom commands, generic MMIO, fixed 30s/300s budgets, MC/DC tool equivalence and fake success.
6. Preserve manifest.json as SSOT. Candidate version 11.2.2 and all 8 Profile ratchets match exact Git source bytes. Protected release and Root promotion are independent downstream gates.
