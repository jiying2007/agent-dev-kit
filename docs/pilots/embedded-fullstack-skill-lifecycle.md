# Pilot: embedded-fullstack-skill-lifecycle

status: evidence-ready

## 目标场景

新增或调整 adk skill，用于嵌入式全栈某个明确能力面，并完成触发冲突、profile 归属、fallback、pilot 和弃用治理。

## 预期路由

- primary: `adk-skill-composition-governance`
- supporting: `adk-runtime-router`, `adk-verification-before-completion`
- fallback: 未使用

## 验证证据

### 原始任务输入

用户要求把 adk 的嵌入式全栈范围从软件层枚举扩展为完整工程闭环，并自行验证推进。

### Skill 生命周期输出

- 新增 skill：`skills/adk-production-field-readiness/SKILL.md`
- Profile 归属：`embedded-fullstack`
- Routing 归属：`production_field_readiness`
- Pilot 归属：`docs/pilots/embedded-production-field-readiness.md`
- Skill 生命周期模板：`templates/skill-lifecycle/adk-skill-lifecycle.md`

### Creation Gate

| Gate | Decision | Evidence |
|---|---|---|
| Duplicate skill checked | pass | `devkit.sh catalog find` 未发现量产/OTA 专属 skill |
| Trigger overlap checked | pass | `check-skill-routing-conflicts.sh` |
| Profile ownership decided | pass | `manifest.yaml:embedded-fullstack` |
| Pilot requirement declared | pass | `docs/pilots/embedded-production-field-readiness.md` |
| Fallback / replaced_by declared | pass | 本 skill 与 `adk-release-versioning` 分工明确，不替代版本策略 |

### 命令证据

| Command | Exit Code | Summary | Evidence |
|---|---:|---|---|
| `rtk bash scripts/devkit.sh match --text "创建新的 skill 并治理触发冲突"` | 0 | routed to `adk-skill-composition-governance` | command output |
| `rtk bash scripts/devkit.sh match --text "量产产测烧录诊断 OTA升级 回滚 现场维护"` | 0 | routed to `adk-production-field-readiness` | command output |
| `rtk scripts/check-skill-routing-conflicts.sh .` | 0 | no skill routing conflicts | command output |
| `rtk bash scripts/check-profile-coherence.sh` | 0 | profile coherence passed | command output |
| `rtk bash tests/test_match_effectiveness.sh` | 0 | 23/23 match effectiveness tests passed | command output |
| `rtk bash tests/run_all.sh` | 0 | full regression passed | command output |

### 残留缺口

本 pilot 证明 adk 原生 skill 生命周期可用；`adk-production-field-readiness` 已补 MCU/SoC 本地 artifact 与 dry-run 证据并升级为 evidence-ready，但仍需要设备、工装、boot log、产测报告和 OTA/rollback 记录后才能声明 production-ready 或升级为 regression-ready。
