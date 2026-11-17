# T3a 实现状态

已冻结独立审查：`report.md`（SHA256 `3871ccde15e12702b80bff03aa58c1fe5ce1dacd0f42f2496df713dc94cd9dff`）、`coverage.json` 和相邻原始结果。2026-11-17 此后切换 implementer；实现自测不算独立终审。

合同入口：`/workspace/scratch/fe8de3b42084/adk-skill-usability/docs/changes/20261117-skill-usability/{requirements,design,tasks}.md`，任务 T3a / U05–U08。写范围仅三个分配的 Skill 与 `tests/test_skill_rtos_methods.py`；共享路由/Manifest/触发测试由 audit_workflow 整合。

Build 前教训检索：`knowledge/L2-domain/lessons.md` 不存在，记录负结果；未伪造历史经验。

使用 skill-creator 的短指令/渐进加载/独立验证原则；本任务是已授权 ADK 源仓修改，不是个人 Skill 安装，不执行其个人目录安装/同步流程。项目规定的 frontmatter 字段、现有验证入口及本轮不 commit/push 边界保持。

## 已完成实现

- RTOS：原 RTA 公式明确要求任务优先级固定且互异；同优先级需另选模型。用现有 implicit_context 限定 RTOS/Zephyr/ThreadX/RT-Thread，明确排除“无 RTOS/没有 RTOS”。
- BSP：仅补带 BSP 的分析/梳理短语，未加入裸“梳理”；implicit_context 为 BSP/SoC，保留原有“SoC board 迁移分析”。压缩重复 description/Goal，没有删减资源链和证据方法。
- IRQ/DMA：non_trigger 改为“无中断且无 DMA 的纯轮询任务”，取消 CPU 预算误排除及 prose slash 拆词。
- RTOS 专属测试增加原模型适用条件检查、互异优先级算术对照及同优先级容量反例；没有新调度器/计算器或 runtime 模拟。

Skill 版本分别为 RTOS 2.0.4、BSP 2.0.2、IRQ/DMA 2.0.3。三个 Skill 源字节总变化为 **-7 B**；测试文件 +1772 B。详情和最终逐文件摘要见 `t3a-source-delta.json`。

## RED → GREEN

| 验收 | RED | 最终 GREEN |
|---|---|---|
| RTOS 专属方法测试 | 5 项中 1 失败，缺互异优先级条件 | 5 项全过，既有 3 个 tick 测试保留 |
| 原 11 条路由验收 | 6/11；RTOS 两误选、BSP 漏选、DMA 两误排除 | 全过 |
| 增补已存在 SoC board 触发的非回归控制 | 首次 BSP-only 领域条件导致 11/12，单一失败 | BSP/SoC 后最终 12/12 |
| claude-code/opencode 导出 | 基线审查各20正文+10reference通过 | 两目标各3正文+3reference写出；最终当前渲染与已写6文件一致 |
| owned diff 空白校验 | — | `git diff --check` exit 0 |

证据：`t3a-rtos-red.log`、`t3a-rtos-green.log`、`t3a-routes-red.json`、`t3a-soc-control-red.json`、`t3a-routes-green.json`、`t3a-exports.json`。补充的失败解释见 `negative-results.md`，最终差异见 `t3a.diff`。

已把最终词和原始路由正反例交给 audit_workflow；共享触发矩阵、Manifest 与最终全量门禁由集成作者处理。本人未改共享文件、未提交或 push。当前为 **T3a 自测完成，等待集成及新的独立 reviewer**。上述 host/静态证据均不提供原生 Agent discovery/load/trigger 或真实 RTOS/设备资格。
