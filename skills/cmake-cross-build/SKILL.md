---
name: cmake-cross-build
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

# cmake-cross-build

## Goal
- 构建稳定可复现的 CMake 交叉编译链路。
- 支持多目标平台（ARM Cortex-M/A、RISC-V）统一构建入口。

## Prerequisites
- 明确 host/build/target 三元组与编译器版本。
- 准备 toolchain file、sysroot、依赖路径映射。
- 安装 CMake >= 3.21 与 Ninja 构建后端。

## Workflow
1. **编写 toolchain 文件**：定义编译器、sysroot、查找路径。
   ```cmake
   # cmake/toolchain-arm-cortex-m4.cmake
   set(CMAKE_SYSTEM_NAME Generic)
   set(CMAKE_SYSTEM_PROCESSOR cortex-m4)
   set(CMAKE_C_COMPILER arm-none-eabi-gcc)
   set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
   set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
   set(CMAKE_OBJCOPY arm-none-eabi-objcopy)
   set(CMAKE_SIZE arm-none-eabi-size)
   set(CMAKE_SYSROOT /opt/arm-sysroot)
   set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
   set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
   set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
   set(CMAKE_C_FLAGS_INIT "-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16")
   set(CMAKE_EXE_LINKER_FLAGS_INIT "-specs=nosys.specs -specs=nano.specs")
   ```
2. **配置 CMakePresets.json**：固化多目标构建矩阵。
   ```json
   {
     "version": 6,
     "configurePresets": [
       {
         "name": "arm-m4-debug",
         "toolchainFile": "cmake/toolchain-arm-cortex-m4.cmake",
         "binaryDir": "build/arm-m4-debug",
         "cacheVariables": { "CMAKE_BUILD_TYPE": "Debug" }
       },
       {
         "name": "arm-m4-release",
         "toolchainFile": "cmake/toolchain-arm-cortex-m4.cmake",
         "binaryDir": "build/arm-m4-release",
         "cacheVariables": { "CMAKE_BUILD_TYPE": "Release" }
       }
     ]
   }
   ```
3. **执行构建**：使用 presets 驱动多目标构建。
   ```bash
   cmake --preset arm-m4-debug
   cmake --build build/arm-m4-debug -j$(nproc)
   ```
4. **构建产物检查**：验证 ELF 架构、段大小、符号表。
   ```bash
   file build/arm-m4-debug/firmware.elf
   arm-none-eabi-size build/arm-m4-debug/firmware.elf
   arm-none-eabi-objdump -h build/arm-m4-debug/firmware.elf
   arm-none-eabi-nm -C --size-sort build/arm-m4-debug/firmware.elf | tail -20
   ```
5. **记录制品与失败点**：输出日志、二进制位置与诊断建议。

## Commands
```bash
# 配置（使用 toolchain 文件）
cmake -S . -B build/<target> -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain-<target>.cmake -G Ninja

# 配置（使用 presets）
cmake --preset <preset-name>

# 构建
cmake --build build/<target> -j$(nproc) --verbose

# 产物检查
file build/<target>/firmware.elf
arm-none-eabi-size build/<target>/firmware.elf

# 测试（host 环境下）
ctest --test-dir build/<target> --output-on-failure

# 清理重建
cmake --build build/<target> --target clean
cmake --build build/<target> -j$(nproc)
```

## Evidence Template
```md
- Toolchain Summary:
  - Compiler: ____ (version ____)
  - Sysroot: ____
  - Target Triple: ____
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

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
