# Pilot: embedded-fullstack-discovery

status: evidence-ready

## 目标场景

面向芯片/板级约束、启动链、BSP、OS/runtime、驱动、组件、协议栈、设备应用、上位机/产测/诊断工具、构建调试、验证、发布、量产和现场维护的需求探索，确认目标层级、接口边界、运行环境、验收方式和验证资源。

## 预期路由

- primary: `adk-requirements-triage`
- supporting: `adk-structured-requirements-questioning`, `adk-task-breakdown`
- fallback: 未使用

## 验证证据

### 原始任务输入

用户指出 `SoC/MCU/Linux/RTOS/驱动/组件/设备应用/上位机工具` 可能过窄，要求把 adk 范围按维度扩展，而不是只列技术名词。

### Discovery 输出

- 范围 SSOT：`docs/reference/embedded-fullstack-scope.md`
- Discovery 模板：`templates/discovery/embedded-discovery-brief.md`
- Skill reference：`skills/adk-requirements-triage/references/embedded-discovery-brief.md`
- 常驻约束层：`docs/embedded-constraints.md`

### 影响层级

- 芯片/板级约束
- 启动链和 BSP/rootfs
- OS/runtime、驱动、组件和协议栈
- 设备侧应用、上位机/产测/诊断工具
- 构建、调试、验证、发布、量产和现场维护
- 安全和可靠性

### 验收标准

| ID | Criterion | Evidence |
|---|---|---|
| AC1 | 范围定义不再局限于软件层枚举 | `docs/reference/embedded-fullstack-scope.md` |
| AC2 | Discovery 模板覆盖板级、启动链、量产和现场约束 | `templates/discovery/embedded-discovery-brief.md` |
| AC3 | 自然语言任务路由到 adk 原生需求澄清 skill | `devkit.sh match --text` |
| AC4 | 更新后通过结构、路由和全量回归验证 | `validate --strict`、`tests/run_all.sh` |

### 命令证据

| Command | Exit Code | Summary | Evidence |
|---|---:|---|---|
| `rtk bash scripts/devkit.sh match --text "嵌入式全栈 boot 到量产现场维护需求目标边界和验收标准不清楚"` | 0 | routed to `adk-requirements-triage` | command output |
| `rtk bash scripts/devkit.sh validate --strict` | 0 | strict validation passed | command output |
| `rtk bash tests/test_match_effectiveness.sh` | 0 | 23/23 match effectiveness tests passed | command output |
| `rtk bash tests/run_all.sh` | 0 | full regression passed | command output |

### 残留缺口

本 pilot 证明 discovery 能力可用；尚未证明具体硬件 bring-up、烧录、OTA 或 HIL 结果可用。硬件相关证据必须由对应 pilot 单独补齐。
