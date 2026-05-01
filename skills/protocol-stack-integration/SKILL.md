---
name: protocol-stack-integration
description: 协议栈接入与状态机整合
triggers:
  - 串口/网络/现场总线协议接入时
non_triggers:
  - 只改 UI 文案
inputs:
  - 协议规范、链路约束
outputs:
  - 集成步骤与状态机草图
constraints:
  - 先定义错误恢复与超时策略
---

# protocol-stack-integration

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
```

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
