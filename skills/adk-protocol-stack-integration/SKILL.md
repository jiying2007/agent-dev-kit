---
name: adk-protocol-stack-integration
description: "用于通信协议栈适配、连接状态机和跨层错误处理的集成设计与回归；不用于纯寄存器布局设计或仅修复孤立格式问题。"
version: 1.0.4
last_updated: 2026-11-15
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

## Goal
- 以可回归方式接入协议栈并稳定运行状态机。

## Prerequisites
- 明确协议版本、时序约束、重传策略和异常语义。
- 确认链路容量与心跳/保活策略。

## Workflow
1. 定义状态机：连接、鉴权、收发、异常恢复全链路。
2. 设计编解码边界：输入校验、长度检查、校验和策略。
3. 超时与重试策略：退避算法、最大重试次数、熔断条件。
4. 兼容策略：协议版本协商与降级路径。
5. 联调验证：正常、乱序、丢包、断链重连场景回归。

## Execution Target Boundary
- 先分类 Linux 用户态、Linux kernel、RTOS/裸机、离线日志或仿真。主动 `tcpdump/tshark` 抓包须有实际接口、权限和数据范围；离线 `tshark` 不要求连接设备，MCU/RTOS 不默认具备这些工具。
- 无主动抓包许可时优先离线已有 trace、脱敏协议日志或仿真测试。丢包/乱序注入、网络配置修改与 live device 测试需要独立授权，不因需求是“集成测试”就自动放宽。
- 链路错误报告按 DNS、TCP/UDP、TLS、协议握手、keepalive 分层标 `measured|inferred|unknown`，抓包数据不得暗示应用根因已确认。

## Commands
离线优先：核实 `PCAP` 来源，以实际问题的 `DISPLAY_FILTER` 分析：
```bash
tshark -n -r "$PCAP" -Y "$DISPLAY_FILTER"
```
主动抓包另需授权及接口/端口/脱敏核实；采样时间与包数取预算内正值，`PCAP` 用本轮新路径。可用项目已有有界入口；下例只在采集成功后分析，失败保留退出码，不消费旧文件：
```bash
tshark -n -i "$IFACE" -f "port $PORT" -a "duration:$CAPTURE_SECONDS" -c "$PACKET_LIMIT" -w "$PCAP" &&
  tshark -n -r "$PCAP" -Y "$DISPLAY_FILTER"
```
保留退出码、帧号/时间及匹配包数。坏文件记读取失败；零字节、合法零包或筛选零匹配即使退出 0 也记 `partial: 无目标协议证据`。大文件按问题限定窗口；`-q` 仅与明确的 `-z` 统计项组合，不单独用作分析。参见 [TShark](https://www.wireshark.org/docs/man-pages/tshark.html)。
Scapy 是 Python API，须在已安装依赖的 Python 环境导入执行，不把 `scapy.all.sniff(...)` 粘入 Bash；发包/注入仍属主动操作。

## Retry and timing boundary
- 分层记录 DNS、TCP、TLS、应用握手和 KeepAlive 的独立 timeout 与状态机。
- timeout/retry/backoff 由实际协议、链路和产品容错预算确定，不套用跨平台通用 30 秒、300 秒及三次重试。
- 非幂等外部操作状态未知时先对账，禁止盲目重复执行。

## 分层测试策略
| 层级 | 测试重点 | 工具 |
|------|----------|------|
| 物理层 | 信号质量、误码率 | 示波器、频谱仪 |
| 链路层 | 帧收发、MAC 仲裁 | 抓包 + 帧注入器 |
| 传输层 | 连接管理、拥塞控制 | tc netem + iperf3 |
| 应用层 | 协议语义、状态机 | 模拟器 + Fuzz 测试 |

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
- 必须包含连接、异常、重连三类状态定义。
- 必须给出有来源、符合目标协议和网络环境的超时及重试参数；未测值标记为待验证。
- 必须有至少 1 个已授权抓包、脱敏日志或模拟器验证证据；目标能力/许可不可用时标记 `not-tested`，不得假称已验证。
