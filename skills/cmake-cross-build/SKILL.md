---
name: cmake-cross-build
description: CMake 交叉编译与多目标构建
version: 1.0.0
last_updated: 2026-05-02
triggers:
  - 新增目标板或 toolchain 时
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

## Prerequisites
- 明确 host/build/target 三元组与编译器版本。
- 准备 toolchain file、sysroot、依赖路径映射。

## Workflow
1. 建立构建矩阵：按目标平台拆分预设与输出目录。
2. 定义 toolchain：编译器、链接器、sysroot、查找路径。
3. 固化构建参数：优化等级、警告级别、开关宏。
4. 执行最小构建：先构建核心目标，再全量目标。
5. 记录制品与失败点：输出日志、二进制位置与诊断建议。

## Commands
```bash
cmake -S . -B build/<target> -DCMAKE_TOOLCHAIN_FILE=<toolchain.cmake>
cmake --build build/<target> -j
ctest --test-dir build/<target>
```

## Evidence Template
```md
- Toolchain Summary:
- Build Matrix:
- Build Result:
- Test Result:
- Known Limitations:
```

## Failure Handling
- 找不到依赖时，优先校验 `CMAKE_FIND_ROOT_PATH` 与 sysroot。
- 链接失败时，先定位 ABI/架构不匹配，再回滚最近构建参数变更。

## Quality Gate
- 必须明确 host/build/target 区分与 toolchain 来源。
- 至少一个目标平台完成构建+测试闭环。
- 构建日志需可复现同一结果。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
