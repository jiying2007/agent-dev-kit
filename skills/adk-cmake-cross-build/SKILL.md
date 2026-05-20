---
name: adk-cmake-cross-build
description: CMake 交叉编译与多目标构建
version: 1.0.0
last_updated: 2026-05-06
triggers:
  - "CMake"
  - "交叉编译"
  - "构建配置"
non_triggers:
  - 与构建无关的需求分析
inputs:
  - toolchain 文件、构建目标
outputs:
  - 构建配置方案
constraints:
  - 必须区分 host/build/target
---

# adk-cmake-cross-build

## Goal
- 构建稳定可复现的 CMake 交叉编译链路。
- 支持多目标平台（ARM Cortex-M/A、RISC-V）统一构建入口。

## Prerequisites
- 明确 host/build/target 三元组与编译器版本。
- 准备 toolchain file、sysroot、依赖路径映射。
- 安装 CMake >= 3.21 与 Ninja 构建后端。

## Workflow
1. **编写 toolchain 文件**：定义编译器、sysroot、查找路径和 ABI flags。
2. **固化 Presets**：用 `CMakePresets.json` 表达目标、构建类型和输出目录。
3. **执行构建**：优先使用 presets；无 presets 时显式传入 toolchain file。
4. **产物检查**：验证 ELF 架构、段大小、符号表和 map 文件。
5. **记录制品与失败点**：输出日志、二进制位置与诊断建议。

## Commands
```bash
cmake -S . -B build/<target> -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain-<target>.cmake -G Ninja
cmake --preset <preset-name>
cmake --build build/<target> -j$(nproc) --verbose
file build/<target>/firmware.elf
arm-none-eabi-size build/<target>/firmware.elf
arm-none-eabi-objdump -h build/<target>/firmware.elf
ctest --test-dir build/<target> --output-on-failure
```

## Evidence Template
```md
- Toolchain Summary:
  - Compiler / Sysroot / Target Triple:
- Build Matrix:
  | Preset | Type | Status | Size |
  |--------|------|--------|------|
  | arm-m4-debug | Debug | PASS/FAIL | __ KB |
  | arm-m4-release | Release | PASS/FAIL | __ KB |
- Build Result: [link to build log]
- ELF Verification: `file` output, section sizes
- Test Result: [ctest summary]
- Known Limitations: [list]
```

## Failure Handling
- 找不到依赖时，优先校验 `CMAKE_FIND_ROOT_PATH` 与 sysroot 完整性。
- 链接失败时，先定位 ABI/架构不匹配（`file *.o`），再回滚最近构建参数变更。
- Presets 解析失败时，检查 CMake 版本与 JSON 语法。
- 交叉编译时 host 工具混入，确保 `find_program` 使用 `CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER`。

## Quality Gate
- 必须明确 host/build/target 区分与 toolchain 来源。
- 至少一个目标平台完成构建+测试闭环。
- 构建日志需可复现同一结果（clean build 验证）。
- ELF 产物必须通过 `file` 命令验证架构正确性。
- toolchain 文件必须纳入版本控制。

---

## 健壮性规范
- 执行前校验 CMake、generator、toolchain、sysroot 和目标 preset。
- 构建失败先定位 ABI/架构/sysroot，不盲目重跑。
- 记录命令、退出码、耗时、产物路径和失败日志。
