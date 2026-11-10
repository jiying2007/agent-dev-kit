# Negative results and source-only boundaries

- 11.2.1 previously passed 115 deterministic matcher cases; 18 additional adversarial prompts identified over-trigger (storage migration, CMake) and under-trigger (MCU fault, FromISR/DMA, DNS). This is purpose-built testing, not population accuracy or real model quality.
- SquashFS read-only or df 100% does not automatically mean corruption. UBIFS readonly incidents require first-error evidence. No destructive UBI experimentation.
- Buildroot may contain CMake. A blanket Buildroot exclusion would be wrong; use actual build system + intended action.
- cyclictest measures thread wakeup scheduling latency, not direct IRQ entry. Linux devmem2 plus Cortex-M NVIC register addresses is not a valid generic example.
- C/C++ scanner success needs an actual negative test. Source snippet cannot certify target CI behavior.
- No physical board, paid model, Codex/Work quota, install or independent field/native certification used in this source change. External model and hardware qualification remain pending.
