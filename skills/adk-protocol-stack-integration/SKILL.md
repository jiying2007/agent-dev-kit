---
name: adk-protocol-stack-integration
description: 协议栈接入与状态机整合
version: 1.0.0
last_updated: 2026-05-06
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

## Commands
```bash
<protocol-simulator-cmd> --scenario reconnect
<packet-capture-cmd> --filter <protocol>
tcpdump -i eth0 -w capture.pcap 'port <port>'
wireshark -r capture.pcap -Y '<protocol>.field == <value>'
tshark -r capture.pcap -T fields -e <protocol>.field1 -e <protocol>.field2
scapy.all.sniff(filter="port <port>", count=100, prn=lambda p: p.summary())
```

## 协议栈分层架构
| 层级 | 职责 | 典型协议 |
|------|------|----------|
| Application | 用户业务逻辑 | MQTT/CoAP/HTTP |
| Session/Security | 加密与鉴权 | TLS/DTLS |
| Transport | 连接与拥塞控制 | TCP/UDP/QUIC |
| Network | 路由与寻址 | IP/IPv6 |
| Link | 帧收发与 MAC | Ethernet/WiFi/BLE |
| Physical | 信号调制 | PHY/射频 |

## 分层测试策略
| 层级 | 测试重点 | 工具 |
|------|----------|------|
| 物理层 | 信号质量、误码率 | 示波器、频谱仪 |
| 链路层 | 帧收发、MAC 仲裁 | 抓包 + 帧注入器 |
| 传输层 | 连接管理、拥塞控制 | tc netem + iperf3 |
| 应用层 | 协议语义、状态机 | 模拟器 + Fuzz 测试 |

## 合理化借口拦截

| 借口 | 现实 | 正确做法 |
|------|------|---------|
| "协议文档看过了不用抓包" | 文档可能有错误或版本差异 | 抓包验证实际行为 |
| "正常流程通了就行" | 异常场景才是协议可靠性的试金石 | 必须测试丢包/乱序/重连 |

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
- 必须给出超时与重试的量化参数。
- 必须有至少 1 个抓包或模拟器验证证据。

---

## 健壮性规范

- **输入验证**: 执行前校验所有必要输入是否存在且格式正确
- **重试策略**: 外部命令失败时最多重试 3 次，指数退避（1s, 2s, 4s）
- **超时控制**: 单步操作超时 30 秒，整体流程超时 300 秒
- **异常隔离**: 单个步骤失败不阻塞其他独立步骤
- **日志记录**: 关键操作记录命令、退出码、耗时
