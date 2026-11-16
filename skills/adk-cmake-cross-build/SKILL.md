---
name: adk-cmake-cross-build
description: "用于嵌入式 CMake 工程的交叉编译、工具链配置与多目标构建排障；不用于无 CMake 的构建系统或直接设备部署。"
version: 1.0.5
last_updated: 2026-11-16
triggers:
  - "CMake"
  - "CMake交叉编译"
  - "CMakePresets"
  - "CMake工具链"
non_triggers:
  - 与构建无关的需求分析
  - Autotools缺少aclocal
  - Makefile-only 工程
inputs:
  - toolchain 文件、构建目标
outputs:
  - 构建配置方案
constraints:
  - 必须区分 host/build/target
---

# adk-cmake-cross-build

## Goal
复现 ARM Cortex-M/A、RISC-V 等实际目标的 CMake 交叉构建。

## Prerequisites
- 核 host/build/target、编译器、toolchain/sysroot、ABI/依赖路径、CMake 版本与 generator；不把其他构建系统转为 CMake。

## Workflow
1. **配置**：核执行授权和工具可用性；未授权只读规划。只用任务自有目录，不替换他人 build。
2. **绑定**：preset 与手工配置二选一。preset 的 build/test 名称可不同，但 `configurePreset`、`binaryDir`、configuration 必须一致；缺匹配 presets 则按核实参数手工配置。见 [Presets](https://cmake.org/cmake/help/v3.27/manual/cmake-presets.7.html)。
3. **后端**：先核 `host-unit | compile-only | emulator | board-runner`，emulator 含 `CROSSCOMPILING_EMULATOR`。没有已验证执行后端用 compile-only；host CTest 不证明板端运行。
4. **产物**：从本次 binaryDir/configuration 定位实际 ELF 为 `ADK_ELF`，不猜 `build/<target>`；用实际目标工具链检查架构、段、符号/map。

## Commands
在源码根选一段；变量须填实际值，目录用绝对路径。`ADK_CONFIG` 固定配置；单配置还设置 `CMAKE_BUILD_TYPE`。`ADK_BUILD_JOBS` 是按 CPU/RAM/CI 配额核定的正整数（`--parallel <resource-budget>`）。
```bash
# preset-build: 已核对 configure/build/test 引用与配置
set -euo pipefail
cmake --preset "$ADK_CONFIGURE_PRESET"
cmake --build --preset "$ADK_BUILD_PRESET" --config "$ADK_CONFIG" --parallel "$ADK_BUILD_JOBS"
case "$ADK_TEST_BACKEND" in
  host-unit|emulator|board-runner) ctest --preset "$ADK_TEST_PRESET" -C "$ADK_CONFIG" --output-on-failure --no-tests=error ;;
  compile-only) printf 'target tests: not-run\n' ;;
  *) exit 2 ;;
esac
```
```bash
# manual-build: 不再执行 preset 配置
set -euo pipefail
cmake -S "$ADK_SOURCE_DIR" -B "$ADK_BINARY_DIR" -G "$ADK_GENERATOR" \
  -DCMAKE_TOOLCHAIN_FILE="$ADK_TOOLCHAIN_FILE" -DCMAKE_BUILD_TYPE="$ADK_CONFIG"
cmake --build "$ADK_BINARY_DIR" --config "$ADK_CONFIG" --parallel "$ADK_BUILD_JOBS"
case "$ADK_TEST_BACKEND" in
  host-unit|emulator|board-runner) ctest --test-dir "$ADK_BINARY_DIR" -C "$ADK_CONFIG" --output-on-failure --no-tests=error ;;
  compile-only) printf 'target tests: not-run\n' ;;
  *) exit 2 ;;
esac
```
成功构建后检查同一产物；`ADK_SIZE/ADK_OBJDUMP` 为已核实的目标工具路径：
```bash
# built-artifact:
set -euo pipefail
file "$ADK_ELF"
"$ADK_SIZE" -A "$ADK_ELF"
"$ADK_OBJDUMP" -h "$ADK_ELF"
```
按实际 build/config/filter 核执行数量；空集/全禁用/筛空须失败，skip/not-run 不算通过。见 [CTest](https://cmake.org/cmake/help/v3.20/manual/ctest.1.html)。

## Evidence Template
```md
- Host / Target / Toolchain / Sysroot:
- Preset Names or Manual Parameters / binaryDir / Configuration:
- Commands / Exit Codes / Duration / Logs:
- ELF Path / Hash / Architecture / Sections / Size:
- Test Backend / Counts / Result / Not-run / Limitations:
```

## Failure Handling
- 依赖失败核 `CMAKE_FIND_ROOT_PATH`/sysroot；链接失败核 ABI/架构，不盲目重跑。
- preset 失败核版本/JSON/引用链；host 工具混入时核 `find_program` 的 `CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER`。

## Quality Gate
- 至少一个目标交叉构建成功；未运行目标测试记 `not-run`，不混用 host/target 或配置的证据。
- clean build 只清理任务自有构建目录；保留可复跑日志，toolchain 纳入版本控制。
- 核 ELF 身份；裸 bin 不能仅靠 `file` 判断 CPU。失败不消费旧产物。
