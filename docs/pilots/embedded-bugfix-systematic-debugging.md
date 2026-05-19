# Pilot: embedded-bugfix-systematic-debugging

status: evidence-ready

## 目标场景

嵌入式驱动、RTOS 任务、构建脚本或发布工具出现可复现异常，需要先复现、提出假设、证伪错误路径、定位根因，再给出最小修复和回归验证。

## 预期路由

- primary: `adk-systematic-debugging`
- supporting: `adk-test-strategy`, `adk-verification-before-completion`
- fallback: 仅当 adk 无法形成根因链路时显式使用

## 验证证据

### 原始任务输入

用户要求补齐 Superpowers systematic-debugging 的根因链路能力，尤其避免先猜修复。

### Runner

```bash
rtk bash scripts/run-embedded-workflow-pilots.sh --pilot bugfix --out /tmp/adk-pilot/embedded-workflow-pilots
```

### Evidence Artifacts

| Artifact | Purpose |
|---|---|
| `reproduction.log` | 复现命令和退出码 |
| `hypotheses.md` | 根因假设 |
| `negative-results.md` | 被证伪假设 |
| `root-cause.md` | 根因和最小修复 |
| `regression.md` | 回归验证 |

### Command Evidence

| Command | Exit Code | Summary | Evidence |
|---|---:|---|---|
| `rtk bash scripts/run-embedded-workflow-pilots.sh --pilot bugfix --out /tmp/adk-pilot/embedded-workflow-pilots` | 0 | 生成复现、假设、负结果、根因、最小修复和回归证据 | `/tmp/adk-pilot/embedded-workflow-pilots/embedded-bugfix-systematic-debugging/evidence.md` |

### 残留缺口

- 仍需绑定真实驱动、RTOS、构建或发布缺陷。
- 本 pilot 证明 debugging 工件链路，不证明具体硬件缺陷已修复。
