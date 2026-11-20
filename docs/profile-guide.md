# Profile 选择指南

Profile 只表示可发现/安装能力，不代表所有 Skill 会常驻模型上下文。权威身份来自根目录 `manifest.json:profiles`；只按当前任务加载一个 primary 和必要的 supporting。

| 场景 | Profile | 能力边界 |
| --- | --- | --- |
| 通用软件开发 | `core` | 需求、设计、计划、调试、验证和评审 |
| 个人项目 | `personal-core` | `core` + 发布检查；记忆、归档和成长复盘按需使用 |
| 通用大型重构 | `large-refactor` | `core` + 长任务执行 + 代码简化；不会隐式装入 BSP/RTOS/OTA |
| 嵌入式全栈 | `embedded-fullstack` | SoC/MCU/Linux/RTOS、驱动、设备、HIL、固件发布与现场能力 |
| 嵌入式大型重构 | `large-refactor` + `embedded-fullstack` | 显式合并通用重构和嵌入式专业能力 |
| 发布加固 | `release-hardening` | 版本、验证、安全和发布准备；真实发布另行授权 |
| 团队交接与长任务 | `team-core` | 任务执行、交接、Pilot、归档等团队专业能力 |
| 线上事故 | `incident-response` | 根因、Core Dump、可靠性和恢复 |
| 外部实践吸收 | `research-intake` | 方法、来源与安全只读审查，不自动采纳 |

Spec 驱动开发使用现有 `docs/runbooks/spec-driven-delivery.md` 和 Workflow，不存在单独的 `openspec-driven` Profile。高风险任务按原门禁升级，不因选择小 Profile 跳过权限或验证。

如目标运行时对多 Profile 叠加的支持未经验证，先用 ADK 的 profile resolve/export 契约核对实际包含的 Skill；不要假定每个原生宿主可以直接叠加。
