# Skill 依赖图

> 2026-05-05 自动生成

## 依赖关系

```
adk-requirements-triage
├── adk-task-breakdown
├── adk-interface-contract-design
│   ├── adk-register-map-design
│   │   └── adk-driver-bringup-checklist
│   │       └── adk-bsp-porting-playbook
│   ├── adk-protocol-stack-integration
│   └── adk-component-api-stability

adk-unit-test-embedded
└── adk-integration-hil-sil
    └── adk-fault-injection-recovery

adk-systematic-debugging
├── adk-toolchain-debug-openocd-gdb
└── adk-performance-profiling-embedded

adk-verification-before-completion
└── adk-commit-pr-quality-gate
    └── adk-release-versioning

独立 skills (无依赖):
- adk-adr-writer
- adk-static-analysis-c-cpp
- adk-rtos-task-design
- adk-interrupt-dma-patterns
- adk-cmake-cross-build
```

## 说明

- depends_on: 该 skill 执行前建议先完成的 skill
- 依赖是建议性的，非强制阻塞
- Agent 可根据实际情况跳过依赖
