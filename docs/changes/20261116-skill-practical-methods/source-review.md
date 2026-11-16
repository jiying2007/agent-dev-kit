# 来源与采用决策

本轮承接 @docs/changes/20261116-skill-execution-fidelity/audit.md 的 65 项 Skill / 118 个入口及直接参考路径覆盖，并针对新的真实缺口深入验证。检索范围包含官方规范、维护者的具体 Skill 文件及其原始技术依据；这是有范围的全网检索，不声称穷尽互联网。来源只用于比较和方法提炼，没有安装或执行第三方 Skill 包。

## 从问题到改动

| 当前任务问题 | 采用的方法 | 采用位置与验证边界 |
|---|---|---|
| review 声明 working-tree / whole-branch，但命令只取 cached patch | diff 端点与目标一致；未跟踪文件、dirty overlay 明确区分 | code-review-loop 既有 evidence reference；执行真实导出命令，断言 patch 内容和 index 不变 |
| 纯 Skill 包不带 ADK 源仓 schema/template | 默认正文自足；源仓辅助资源须先核根目录与可读性 | context-engineering / context-compress-handoff；实际两目标 core export，无重复资源副本 |
| ADC 12-bit 样例测试掩盖更大输入乘法溢出 | 先拓宽中间量，声明 int 支持范围，用端点/钳位作独立预期 | 原示例及既有 command-example 测试；host native / UBSan，不是板端验证 |
| “堆用 memcheck”未区分峰值与内存错误 | Massif 对应堆峰值/时间线/分配点；Memcheck 对应错误/泄漏，RSS 单独量 | performance-profiling-embedded 原工具映射；本机 Valgrind 缺失，不称实测 |
| 新进程重复不能重现同进程前序污染 | 条件性保留 suite 顺序、seed、worker、进程边界，做污染前序/反序对照 | flaky 现有按需 reference；原始状态模型只说明诊断维度 |
| 分段 timeout 和次数上限不保证整体时限 | 阶段、重试及退避共用剩余预算；核已有 SDK 重试及总调用量 | protocol 原 Retry boundary；整数假时钟不是网络/设备测量 |
| preset 配置目录与后续 build/test/artifact 不一致 | 互斥的 preset/manual 路径，绑定真实 binaryDir、configuration 与 ELF | cmake-cross-build；本地静态反例，真实 fixture 需具备 CMake 的平台执行 |

## 一手来源

检索日期：2026-11-16。仓库来源固定到实际读取的 commit；动态官方文档不虚构 commit。完整研究及原始反例保存于本 change 的 evidence。

| 来源 | 固定身份或官方地址 | 采用或保留 |
|---|---|---|
| Git diff 官方文档 | https://git-scm.com/docs/git-diff | cached、HEAD 工作树、已核基线与 HEAD 的端点语义；无默认基线猜测 |
| Agent Skills specification | https://agentskills.io/specification | Skill 目录与随包资源、按需加载；不把消费端当源仓 |
| Valgrind 工具说明 | https://valgrind.org/info/tools.html | Memcheck 与 Massif 的用途区别 |
| Massif 官方手册 | https://valgrind.org/docs/manual/ms-manual.html | 堆随时间变化、分配来源、采样局限；不把堆口径当 RSS |
| CMake presets 官方文档 | https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html | build/test preset 经 configurePreset 关联配置，名称无需相同 |
| Microsoft testfx / test-anti-patterns | [SKILL.md](https://github.com/microsoft/testfx/blob/74be6a61c1324c7b4810841ba2716040b47230f4/.agents/skills/test-anti-patterns/SKILL.md)，blob `5641f2ac231e8a2784d572f13b4be4798994d55d` | 只补本次查到的顺序依赖诊断；已有独立 oracle / mock 边界保持 |
| GitHub awesome-copilot / cloud-design-patterns | [SKILL.md](https://github.com/github/awesome-copilot/blob/97d89fa3a1fdd84cc7d6c42fe82dbbf8ff2e3c20/skills/cloud-design-patterns/SKILL.md)，blob `b9a17433b9bedf95947bfe6624ef0a4bfa053021`；[reliability-resilience.md](https://github.com/github/awesome-copilot/blob/97d89fa3a1fdd84cc7d6c42fe82dbbf8ff2e3c20/skills/cloud-design-patterns/references/reliability-resilience.md)，blob `208b92d8697abb62f4396c889640ba19c913a19c` | Retry 的短暂/永久失败与幂等性；不引入整套云模式词典 |
| Microsoft Azure Architecture Center | [transient-faults.md](https://github.com/MicrosoftDocs/architecture-center/blob/13861343a03580f08556f9eddf44a3223e01cfa0/docs/best-practices/transient-faults.md)，blob `165c153f14fc4870f5f088e8b31b126e821a95af`；[官方发布页](https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults) | 总时延包含 timeout 与等待；识别重叠重试，尊重 Retry-After |
| AWS Builders Library | https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/ | 阶段覆盖、多层放大、backoff/jitter；不直接套云平台参数 |
| GitHub awesome-copilot / test-gap-audit | [SKILL.md](https://github.com/github/awesome-copilot/blob/97d89fa3a1fdd84cc7d6c42fe82dbbf8ff2e3c20/skills/test-gap-audit/SKILL.md)，blob `31ea9fa996bf9efa3343a70f95efda34a1eb8cd7` | 已有风险选择和真实行为断言，不新增相似审计入口 |
| humanlayer / design-control-loop | [SKILL.md](https://github.com/humanlayer/skills/blob/4d69d20f6e9b57b4fcf0d501ccfb1be961f0f329/plugins/design-control-loop/skills/design-control-loop/SKILL.md)，blob `c9abc1b884d6002b4b76a7f611cf7686e91d59c8` | 本地反馈与单一信息源已有覆盖；不引入定时 CI、外部 headless agent 或新凭据 |

## 推论和拒绝项

剩余预算取最小值、本地单调时钟边界、同进程前序/反序矩阵，是针对 ADK 现有缺口的设计推论，不冒充外部 Skill 的逐字内容。已覆盖项保留现状，不因外部仓库流行度或 Skill 数量增加重复资产。

本轮不调用外部模型/API、Codex/ChatGPT Work CLI/Cloud 额度，不新增定时任务或真实设备变更。逻辑反例、源码回归、host 编译、真实 CI 与模型效果分别记录；模型成功率、Token、费用和板端性能仍未测量。
