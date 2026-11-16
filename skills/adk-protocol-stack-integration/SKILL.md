---
name: adk-protocol-stack-integration
description: "用于通信协议栈适配、连接状态机和跨层错误处理的集成设计与回归；不用于纯寄存器布局设计或仅修复孤立格式问题。"
version: 1.0.5
last_updated: 2026-11-16
triggers:
  - "协议栈"
  - "协议集成"
non_triggers:
  - 只改 UI 文案
inputs:
  - 协议规范、链路约束
outputs:
  - 集成步骤与状态机草图
constraints:
  - 先定义错误恢复与超时策略
---

# adk-protocol-stack-integration

## Workflow
1. 核协议版本、时序、链路容量、重传/异常语义及保活；定义连接、鉴权、收发、恢复状态机。
2. 明确输入、长度、校验和、版本协商与降级边界。
3. 按下述预算设计 timeout/retry/backoff、熔断与恢复；回归正常、乱序、丢包、断链重连。

## Execution Target Boundary
- 区分 Linux 用户态/kernel、RTOS/裸机与离线/仿真。主动 `tcpdump/tshark` 须核接口、权限和数据范围；MCU/RTOS 不默认具备工具，离线分析无需设备。
- 无主动许可用已有 trace、脱敏日志或仿真；丢包/乱序注入、网络配置与 live device 测试须独立授权。
- 按 DNS、TCP/UDP、TLS、握手、keepalive 标 `measured|inferred|unknown`；抓包不能独证应用根因。

## Commands
离线优先，核 `PCAP` 来源与 `DISPLAY_FILTER`：
```bash
tshark -n -r "$PCAP" -Y "$DISPLAY_FILTER"
```
主动采集须授权并核接口/端口/脱敏；时间、包数取预算内正值，`PCAP` 用新路径。优先项目有界入口；以下只分析采集成功的新文件，失败留退出码：
```bash
tshark -n -i "$IFACE" -f "port $PORT" -a "duration:$CAPTURE_SECONDS" -c "$PACKET_LIMIT" -w "$PCAP" &&
  tshark -n -r "$PCAP" -Y "$DISPLAY_FILTER"
```
保留退出码、帧号/时间、匹配包数。坏文件记失败；零字节、零包或零匹配即使 exit 0 也记 `partial: 无目标协议证据`。大文件限窗口；`-q` 只配明确的 `-z` 统计。参见 [TShark](https://www.wireshark.org/docs/man-pages/tshark.html)。Scapy 是 Python API，需已装依赖的 Python 环境，不能粘入 Bash；发包/注入仍属主动操作。

## Retry and timing boundary
- DNS、TCP、TLS、应用及 KeepAlive 保留独立 timeout/状态机；参数依据协议、链路与产品预算，不套固定秒数或次数。
- 对有完成时限的操作，用本地单调钟计算剩余预算，阶段、尝试和退避均计入；每阶段限于本地 timeout 与剩余时长的较小者，耗尽不再尝试。跨主机传剩余时长或协议定义的 deadline，不传本地单调钟绝对值；长连接寿命另定。
- 核 SDK/调用层已有重试，明确应用重试责任层及总 attempts（含首次）；多层确需重试则核总调用量/时延，不关闭协议必要重传。按错误语义区分短暂/永久失败；非幂等 UNKNOWN 先对账，不盲重放。退避/jitter 遵守协议时序及 Retry-After；超过剩余预算先结束本轮，业务延后另按语义处理，不延长已耗尽时限或缩短强制等待。
- 用已核实现/仿真检查正常、短暂故障后成功、永久失败、退避耗尽、嵌套重试；未执行不计验证。按问题选物理测量、帧分析、传输或应用测试。

## Evidence Template
```md
- State Machine:
- Timeout/Retry Policy:
- Error Recovery:
- Compatibility Strategy:
- Integration Test Result:
```

## Failure Handling
- 若协议行为与文档冲突，先记录证据并冻结接口扩展。
- 若断链重连不稳定，降低并发并回到最小报文流程定位。

## Quality Gate
- 定义连接、异常、重连；超时/重试参数有来源并匹配目标环境，未测值标待验证。
- 至少 1 个已授权抓包、脱敏日志或模拟器证据；能力/许可不可用记 `not-tested`。
