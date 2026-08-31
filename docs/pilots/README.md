# Pilot 证据库

## 目标

本目录记录 ADK 原生能力在真实或准真实任务中的运行证据，用于验证路由、执行、制品与设备 readiness；外部参考仓不进入运行兼容路径。

adk 的 pilot 以嵌入式全栈开发为主，覆盖芯片/板级约束、启动链、BSP、OS/runtime、驱动、组件、设备侧应用、上位机/产测/诊断工具、构建调试、验证、发布、量产和现场维护。通用语言或脚本样例只有在服务嵌入式交付链路时才纳入，不扩展到通用 Web、互联网后端或云原生。

## 证据分级

| 状态 | 含义 | 是否可用于运行证据 |
|---|---|---|
| planned | 已定义要跑的 pilot，但没有真实执行证据 | 否 |
| evidence-ready | 有任务输入、执行记录和验证命令 | 是 |
| regression-ready | 已加入 match 或测试回归 | 是 |
| rejected | 任务证明当前能力不足，需要补缺口 | 否 |

## Readiness 维度

`index.tsv` 同时记录三类 readiness，避免把“流程证据已准备好”误读成“设备可量产”：

| 维度 | 含义 |
|---|---|
| workflow_readiness | adk workflow / skill 是否能按预期路由、执行和复跑 |
| artifact_readiness | 生成物、报告、脚本入口、证据索引是否足以支撑工程审计 |
| device_readiness | 设备侧证据是否闭环；`simulated-pass` 只表示模拟设备状态机通过，不等于真实硬件放行 |

可选值：`pass`、`partial`、`pending`、`needs-fix`、`simulated-pass`、`not-applicable`。

## 最小记录项

- 任务输入和背景。
- primary skill、supporting skill、内部降级裁决。
- 是否使用内部 fallback，若使用必须说明原因；不得把外部参考仓作为 fallback provider。
- 执行摘要、验证命令、退出码和证据路径。
- 漏匹配、误匹配、流程过重或流程不足的结论。

## 维护规则

- `index.tsv` 是 pilot 清单。
- `planned` 不能作为下线证据。
- `evidence-ready` 只代表 pilot 证据成熟；若 `device_readiness=needs-fix` 或 `simulated-pass`，不得声明真实设备 production-ready。
- 每次修改 `index.tsv` 或 evidence 文件后运行 `bash scripts/pilot-readiness.sh`；需要门禁摘要时运行 `bash scripts/pilot-readiness.sh --summary-json`。
- 嵌入式全栈 pilot 优先覆盖芯片/板级、启动链、BSP/rootfs、Linux/RTOS、驱动、组件、设备应用、上位机/产测/诊断工具、交叉编译、QEMU/SIL、HIL、静态分析、故障注入、完成前验证、发布收口、OTA/回滚和现场维护。
