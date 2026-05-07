# Skill 依赖图

> 2026-05-05 自动生成

## 依赖关系

```
gdk-requirements-triage
├── gdk-task-breakdown
├── gdk-interface-contract-design
│   ├── gdk-register-map-design
│   │   └── gdk-driver-bringup-checklist
│   │       └── gdk-bsp-porting-playbook
│   ├── gdk-protocol-stack-integration
│   └── gdk-component-api-stability

gdk-unit-test-embedded
└── gdk-integration-hil-sil
    └── gdk-fault-injection-recovery

gdk-systematic-debugging
├── gdk-toolchain-debug-openocd-gdb
└── gdk-performance-profiling-embedded

gdk-verification-before-completion
└── gdk-commit-pr-quality-gate
    └── gdk-release-versioning

独立 skills (无依赖):
- gdk-adr-writer
- gdk-static-analysis-c-cpp
- gdk-rtos-task-design
- gdk-interrupt-dma-patterns
- gdk-cmake-cross-build
```

## 说明

- depends_on: 该 skill 执行前建议先完成的 skill
- 依赖是建议性的，非强制阻塞
- Agent 可根据实际情况跳过依赖
