# Pilot: embedded-tdd-test-strategy

status: evidence-ready

## 目标场景

新增或调整嵌入式公共逻辑、驱动适配层、构建脚本、上位机工具或发布链路时，使用 `adk-test-strategy` 判定 Level 0/1/2，并在 Level 2 场景保留红灯和绿灯证据。

## 预期路由

- primary: `adk-test-strategy`
- supporting: `adk-unit-test-embedded`, `adk-verification-before-completion`
- fallback: 仅当通用 TDD 流程无法覆盖项目测试入口时显式使用

## 验证证据

### 原始任务输入

用户要求补强嵌入式测试矩阵，覆盖 C/C++ host unit、CMake/ctest、交叉编译 smoke、QEMU/SIL、HIL 手工记录、静态分析与故障注入组合。

### Runner

```bash
rtk bash scripts/run-embedded-workflow-pilots.sh --pilot test-strategy --out /tmp/adk-pilot/embedded-workflow-pilots
```

### Evidence Artifacts

| Artifact | Purpose |
|---|---|
| `test-matrix.md` | Level 0/1/2 和硬件缺口判定 |
| `fixtures/host-unit-red.log` | 红灯失败输出 |
| `fixtures/host-unit-green.log` | 绿灯验证输出 |
| `fixtures/ctest.log` | CMake/ctest 入口样例 |
| `fixtures/cross-build-smoke.log` | 交叉编译 smoke 样例 |
| `fixtures/qemu-sil.log` | QEMU/SIL stub 样例 |
| `fixtures/hil-manual-record.md` | HIL 手工记录模板 |

### Command Evidence

| Command | Exit Code | Summary | Evidence |
|---|---:|---|---|
| `rtk bash scripts/run-embedded-workflow-pilots.sh --pilot test-strategy --out /tmp/adk-pilot/embedded-workflow-pilots` | 0 | 生成 Level 0/1/2 矩阵、红绿证据、ctest、cross-build、QEMU/SIL 和 HIL 记录 | `/tmp/adk-pilot/embedded-workflow-pilots/embedded-tdd-test-strategy/evidence.md` |

### 残留缺口

- 仍需接入真实项目的 CMake/ctest、交叉编译器和 HIL 设备。
- 本 pilot 保留红绿路径和不可自动化项，但不声明硬件覆盖完成。
