# Skill 依赖图

> 2026-05-05 自动生成

## 依赖关系

```
requirements-triage
├── task-breakdown
├── interface-contract-design
│   ├── register-map-design
│   │   └── driver-bringup-checklist
│   │       └── bsp-porting-playbook
│   ├── protocol-stack-integration
│   └── component-api-stability

unit-test-embedded
└── integration-hil-sil
    └── fault-injection-recovery

systematic-debugging
├── toolchain-debug-openocd-gdb
└── performance-profiling-embedded

verification-before-completion
└── commit-pr-quality-gate
    └── release-versioning

独立 skills (无依赖):
- adr-writer
- static-analysis-c-cpp
- rtos-task-design
- interrupt-dma-patterns
- cmake-cross-build
```

## 说明

- depends_on: 该 skill 执行前建议先完成的 skill
- 依赖是建议性的，非强制阻塞
- Agent 可根据实际情况跳过依赖
