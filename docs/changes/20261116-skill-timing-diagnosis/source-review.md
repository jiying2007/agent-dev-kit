# 外部方法：固定来源与采用边界

用户要求继续检索成熟 Skills。本轮先对照现有方法，再用官方 API、实现或可执行探针核查候选。外部 Skill 不整体导入；错误示例不采纳。来源文件的 SHA256、阅读范围和许可核对在三组原始审查中保留。

| 分组 | 固定来源文件 | 判断 / 核查用途 |
|---|---|---|
| core | [anthropics/skills / skills/skill-creator/SKILL.md](https://github.com/anthropics/skills/blob/1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064/skills/skill-creator/SKILL.md) | 具体采用/拒绝理由见该组原始审查的 external_decisions；不复制外部生产实现。 |
| core | [mattpocock/skills / skills/productivity/grilling/SKILL.md](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/productivity/grilling/SKILL.md) | 具体采用/拒绝理由见该组原始审查的 external_decisions；不复制外部生产实现。 |
| core | [obra/superpowers / skills/systematic-debugging/SKILL.md](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/systematic-debugging/SKILL.md) | 具体采用/拒绝理由见该组原始审查的 external_decisions；不复制外部生产实现。 |
| core | [git/git / builtin/bisect.c](https://github.com/git/git/blob/9a2fb147f2c61d0cab52c883e7e26f5b7948e3ed/builtin/bisect.c) | 具体采用/拒绝理由见该组原始审查的 external_decisions；不复制外部生产实现。 |
| core | [git/git / Documentation/git-bisect.adoc](https://github.com/git/git/blob/9a2fb147f2c61d0cab52c883e7e26f5b7948e3ed/Documentation/git-bisect.adoc) | 具体采用/拒绝理由见该组原始审查的 external_decisions；不复制外部生产实现。 |
| core | [anthropics/skills / skills/skill-creator/LICENSE.txt](https://github.com/anthropics/skills/blob/1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064/skills/skill-creator/LICENSE.txt) | 具体采用/拒绝理由见该组原始审查的 external_decisions；不复制外部生产实现。 |
| core | [mattpocock/skills / LICENSE](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/LICENSE) | 具体采用/拒绝理由见该组原始审查的 external_decisions；不复制外部生产实现。 |
| core | [obra/superpowers / LICENSE](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/LICENSE) | 具体采用/拒绝理由见该组原始审查的 external_decisions；不复制外部生产实现。 |
| embedded | [Jeffallan/claude-skills / skills/embedded-systems/SKILL.md](https://github.com/Jeffallan/claude-skills/blob/078a25cc5bfd8011459be7b91d004e900c1d02d3/skills/embedded-systems/SKILL.md) | 借鉴按问题加载参考的组织方式（ADK已有）；拒绝直接移植ISR/IRQ模板、固定优先级/栈水位门槛及不检查所有返回值的示例。 |
| embedded | [Mindrally/skills / embedded-stm32/SKILL.md](https://github.com/Mindrally/skills/blob/7682ca77710e0971eab4e0ae5dddfa281aea0ba5/embedded-stm32/SKILL.md) | 借鉴generated/user边界、资源所有权与分层测试（ADK已有）；拒绝同一RX buffer在消费者读取前重新交给DMA的示例，也不跨MCU套用CFSR/HFSR。 |
| embedded | [rovinax/embedded-skills / skills/embedded-rtos-design/SKILL.md](https://github.com/rovinax/embedded-skills/blob/022ce31b469b1a1d0c1261c2c8d0f3e07b2c0bbc/skills/embedded-rtos-design/SKILL.md) | 采用固定周期意图，经官方API纠正；拒绝双参osDelayUntil、ticks=ms、固定任务优先级/禁止所有ISR控制计算和无条件拆任务。 |
| embedded | [FreeRTOS/FreeRTOS-Kernel / include/projdefs.h](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/ca759444e9ca59cfa3a9faa6cb8b49e0772ca520/include/projdefs.h) | 核默认pdMS_TO_TICKS整数除法、宏可覆盖及最终TickType_t收窄；真实头文件编译运行30向量。 |
| embedded | [FreeRTOS/FreeRTOS-Kernel / include/task.h](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/ca759444e9ca59cfa3a9faa6cb8b49e0772ca520/include/task.h) | 核相对vTaskDelay与绝对xTaskDelayUntil、previous wake更新和return值只表示是否阻塞。 |
| embedded | [FreeRTOS/FreeRTOS-Kernel / tasks.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/ca759444e9ca59cfa3a9faa6cb8b49e0772ca520/tasks.c) | 只审读xTaskDelayUntil实现，确认到点now==wake时pdFALSE、每次均推进previous wake；本地保存对应原始函数摘录。 |
| embedded | [FreeRTOS/FreeRTOS-Kernel / include/timers.h](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/ca759444e9ca59cfa3a9faa6cb8b49e0772ca520/include/timers.h) | 核xTimerStop/Delete pdPASS仅成功投递timer command queue，不证明共享回调context已无使用者。 |
| embedded | [FreeRTOS/FreeRTOS-Kernel-Book / ch06.md](https://github.com/FreeRTOS/FreeRTOS-Kernel-Book/blob/ba20b2f820926587d5ee20ce312b3789d63f795c/ch06.md) | 审读6.2、6.4及命令入队语义；FreeRTOS timer callback共享daemon task且不能进入Blocked。 |
| embedded | [ARM-software/CMSIS_6 / CMSIS/RTOS2/Include/cmsis_os2.h](https://github.com/ARM-software/CMSIS_6/blob/69b5aa343e618b74ffb40ca2b13f73a0cda7ab76/CMSIS/RTOS2/Include/cmsis_os2.h) | 核osDelayUntil单absolute-tick参数；用实际头文件编译确认双参错误和单参合法。 |
| embedded | [torvalds/linux / Documentation/core-api/dma-api-howto.rst](https://github.com/torvalds/linux/blob/aebb7274476403040d582c61478df8f4a7bf9cd3/Documentation/core-api/dma-api-howto.rst) | 审读coherent DMA与ordering段；现ADK明确memory ordering，作为保留依据，不额外扩写。 |
| optional | [cloudflare/skills / skills/workers-profiling/SKILL.md](https://github.com/cloudflare/skills/blob/cbf893b954222276bf1af57e5f23379231e0efb9/skills/workers-profiling/SKILL.md) | 实际部署版本、profile source map和采样证据支持最小改动的方法与现有实运行身份/符号映射边界相符；不引入Cloudflare专属CLI或产品路由。 |
| optional | [supabase/agent-skills / skills/supabase-postgres-best-practices/SKILL.md](https://github.com/supabase/agent-skills/blob/c9be0e931b7930f7d02126d04774d904c381e7d7/skills/supabase-postgres-best-practices/SKILL.md) | Postgres专属规则不属于现有ADK嵌入式技能职责；按影响分类与按需读reference已存在，不新增数据库skill或强制广触发。 |
| optional | [github/awesome-copilot / skills/incident-postmortem/SKILL.md](https://github.com/github/awesome-copilot/blob/dc0083dbe22133bfa7ce3500dee85e187e0cd47a/skills/incident-postmortem/SKILL.md) | 可按需吸收UTC时间线与检测/缓解/预防行动区分；不采用每次必做鱼骨/5Why、逐节阻塞追问、固定输出目录或外部转换安装。 |
| optional | [wshobson/agents / plugins/incident-response/skills/postmortem-writing/SKILL.md](https://github.com/wshobson/agents/blob/9c61ab243def98f72da12abd41cfcf5bcd91af9d/plugins/incident-response/skills/postmortem-writing/SKILL.md) | 保留基于证据的简短RCA，不吸收强制五层追问、固定会议/日程或把文档与测试缺失机械判根因；细节下沉方法现已存在。 |
| optional | [open-telemetry/opentelemetry-specification / specification/logs/data-model.md](https://github.com/open-telemetry/opentelemetry-specification/blob/a4e05d9704fc5218d85a4154fb5b143ea3f5340e/specification/logs/data-model.md) | 事件发生Timestamp与采集ObservedTimestamp语义不同；可补齐时间来源和时区/时钟偏差边界，不能用观察顺序制造因果。 |

## 本轮吸收

- 系统调试：不可测修订与目标回归分开；受控 bisect 退出码、歧义区间与重跑前保存原始故障产物。
- RTOS：单位/量化/范围、绝对周期和超期策略、共享 timer 服务与取消生命周期。
- RCA：事件时间和采集时间、时区与时钟偏差，按实际缺口选择检测/缓解/预防行动。
- 生命周期模板的空白结论由本地解析直接发现，默认待验证；不归因于外部效果实验。

## 明确拒绝

社区示例中的双参数 CMSIS `osDelayUntil`、tick 当毫秒、未保存原状态便无条件开启 IRQ、DMA 消费前重用同一缓冲区，不作为可执行推荐。固定优先级、固定水位百分比和云平台专用工具也不跨目标复制。Linux coherent DMA 的顺序约束现有 Skill 已覆盖，因此保留，不重复扩写。
