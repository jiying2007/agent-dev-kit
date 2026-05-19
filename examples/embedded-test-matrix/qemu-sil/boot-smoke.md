# QEMU/SIL Boot Smoke

- command: `qemu-system-arm -M lm3s6965evb -kernel build/firmware.elf -nographic`
- expected_log:
  - `boot: start`
  - `scheduler: ready`
  - `adc task: initialized`
- status: stub

Replace the stub command with the project-specific board model or simulator.
