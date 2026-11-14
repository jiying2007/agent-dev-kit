# 交叉编译故障与工具适用性

只读定位本例的第一条故障并给出下一步最小检查，不运行构建、网络安装或板端命令。实际 package infra、配置、log 与 target 已给出；不得仅凭“交叉编译”改为 CMake，也不得把 MCU 当 Linux 进程。

输出 `diagnosis.json`：`build_system`、`first_failure`（原 log 中错误字符串）、`failure_layer`（host / target）、`next_probe`（kind 与 tools 数组）、`build_status`。再输出 `target-probes.json`，按 linux-embedded / mcu-rtos 顺序各给 `target`、`probe`、`measured`：本任务 Linux 用户态 latency 取 perf，MCU cycle 取 DWT；都未实测。不要编辑原输入或把 compile-only 结论升级为 board-runner 通过。
