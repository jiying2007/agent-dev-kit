---
name: adk-static-analysis-c-cpp
description: "用于 C/C++ 静态分析告警分级、根因追踪与误报确认，并补最小复现；不用于把单次扫描当作完整功能或动态安全验收。"
version: 1.0.5
last_updated: 2026-11-15
triggers:
  - "静态分析"
  - "代码检查"
  - "lint"
non_triggers:
  - 快速原型验证
inputs:
  - 代码路径、规则集
outputs:
  - 缺陷报告与修复建议
constraints:
  - 高优先级缺陷必须阻断合并
---

# adk-static-analysis-c-cpp

## Goal
定位静态缺陷，给出可复验的修复与误报依据。

## Prerequisites
确认编译数据库、分析配置和规则严重级别。

## Target Eligibility（按目标分流，非一次跑全部工具）
- `linux-embedded`：核 kernel/userspace、交叉编译数据库、sysroot；只选目标/宿主支持的工具。
- `mcu-rtos`：核 RTOS、MCU ABI、编译器、链接脚本、构建变体；Zephyr 的 Kconfig/Devicetree 不通用于其他工程。
- `mcu-baremetal`：按无 libc/宿主 OS 的约束选择告警、ELF/map、MISRA 和静态路径，不默认存在进程或文件系统。
- 缺匹配的 compile_commands/toolchain、target 或授权，标 `not-applicable / not-scanned`；零告警不等于零缺陷。安装、许可证、固件写入需独立权限。

## Workflow
1. 规则基线设定：按项目风险选择规则集。
2. 源变化选对应 translation units（TU）；头文件按依赖文件/构建图选消费者 TU，规则/宏/构建变化选受影响目标。范围无法证明时扫该目标完整编译数据库，不能跳过仅 `.h/.hpp` 的变化。
3. 带 TU、target flags、header filter 扫描，输出位置、规则与级别；头文件不能脱离构建上下文单独分析。
4. 去噪与归因：剔除误报并保留依据。
5. 整改优先级：优先处理内存安全、并发、未定义行为问题。
6. 回归确认：修复后重跑受影响 TU 并比对残留问题，不以过滤修改行代替完整路径分析。

## Commands
路径来自真实构建；规则按 `.clang-tidy`、cppcheck/PVS 配置选择，不一次运行全部工具：
```bash
clang-tidy -p build src/example.c
cppcheck --enable=warning,style,performance --project=compile_commands.json
```

## 缺陷严重级别映射
按项目风险映射：Blocker（越界/UAF/空指针）阻断；Major（溢出/未初始化/泄漏）按 SLA 整改；Minor 风格与 Info 优化按需处理，不设通用时限。

## CI 集成示例

按受信 `BASE_SHA/HEAD_SHA` 和构建依赖选 TU；纯文档可不扫描，仅无 .c/.cpp 变化不够。以下适用 Ubuntu/CMake：用真实 preset/toolchain 生成数据库，缺依赖映射时分析全部 TU；不同工具规则不可替代。
```yaml
static-analysis:
  steps:
    - run: cppcheck --enable=warning --error-exitcode=1 --project=build/compile_commands.json
    - run: |
        set -euo pipefail
        python3 - <<'PY' | xargs -0 -r clang-tidy -p build --header-filter='.*' --warnings-as-errors='*'
        import json, os, sys
        from pathlib import Path
        rows = json.loads(Path('build/compile_commands.json').read_text())
        paths = sorted({str((Path(row['directory']) / row['file']).resolve(strict=True)) for row in rows})
        if not paths:
            raise SystemExit('no translation units: not-scanned')
        for path in paths:
            sys.stdout.buffer.write(os.fsencode(path) + b'\0')
        PY
```

核数据库、规则、完成的 TU 与头文件范围；空库、缺工具、解析失败记 `not-scanned`。用仅改头文件的已知告警验证 CI 非零。PR/fork 保持受信触发与 secret 隔离。依据：https://clang.llvm.org/extra/clang-tidy/ 。
## Evidence Template
```md
- Rule Set:
- Scan Summary (B/M/m):
- Top Blockers:
- False Positive Notes:
- Re-scan Delta:
```

## Quality Gate
blocker 清零或有批准豁免，major 有整改计划与 owner；误报/抑制须留依据。结果可复跑可比对；配置故障先修复，不能将未扫描记成功。
