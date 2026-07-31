# Embedded Remote ADB/HIL Hardening Proposal

## Problem

远程嵌入式调试当前只描述通道和日志取证，缺少分层连通性、`adb connect` 输出语义、失联熔断、制品身份、受控部署前置条件、HIL 分阶段扩大和健康恢复契约。`adk-runtime-router` 还引用了不适用于下游 `~/codex` 的旧命令。

## Goal

- 把远程设备健康拆成 route/network hint、transport、shell、app/diag 四层。
- 默认只读取证，设备失联时停止写入和无界重试。
- 将 artifact identity、backup anchor、mutation authority 和 postcondition 纳入门禁。
- 固化 single smoke -> short cycle -> long stress -> soak -> restore 的 HIL 扩大顺序。
- 把 runtime-router 下游命令更新为当前受信的 `~/codex` skill-search 和 routing eval。

## Non-goals

- 不绑定 PCR02、SigmaStar、具体 IP、进程名或设备路径。
- 不提供自动部署、自动回滚、电源控制或串口控制实现。
- 不修改直接 tool target、安装器或发布协议。

## Acceptance

- skill 正文包含独立探测、输出语义、熔断、身份、HIL、恢复和证据 bundle 契约。
- runtime-router 不再引用下游不存在的脚本。
- strict validation 和相关内容检查通过。
