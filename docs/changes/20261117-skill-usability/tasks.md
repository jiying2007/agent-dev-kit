# 当前状态与任务

阶段：Spark / Design / Build 完成；三组已覆盖全部 65 项并冻结审查、RED 和实现自测。进入整合验证及新的独立 Spec/Quality review；尚未发布或完成 Root 消费。

| 任务 | 状态 | verify / 证据 |
| --- | --- | --- |
| T1 冻结当前源码、恢复验证环境并分组全部 Skill | 完成 | 新 checkout HEAD 为 78c3be7；Manifest 56 core + 9 optional；分组 20 + 25 + 20 |
| T2 独立审查 65 项并选择具体反例 | 完成 | baseline 20 + 25 + 20；context/optional 初次导出覆盖概括的更正单独追加，不覆盖原始记录 |
| T3a 嵌入式适用条件与触发边界（U05–U08） | 实现及自测完成 | 互异/同级 RTA、BSP/SoC 正例、RTOS 域外与 IRQ/DMA 正反例 |
| T3b review/设备路由与机器交接（U01–U04） | 实现及自测完成 | 真实 matcher；canonical 19 字段 validator 接收与错误类型拒绝；两个实际 compiler 输出 |
| T3c 导出依赖、完整盘点、只读到实施交接（U09–U10） | 实现及自测完成 | helper 缺席边界、65 项 catalog 并集、只读交接和人类信封映射；原 8 个预算未抬限 |
| T4 整合验证与独立 Spec/Quality 审查 | 进行中 | exact-source 证据、真实失败记录、独立报告 |
| T5 完成组件 PR、main CI 和不可变 Release | 待 T4 | 精确源身份、发布档案、原生证明 |
| T6 Root source-only 接入和实际 main CI 核验 | 待 T5 | 两路径差异、原生消费及签名 CI 收据 |

恢复入口：先读本文件，再读 T2 的原始审查证据；上一轮结论见 `docs/changes/20261117-skill-scope-methods/`，已修内容不重复计入新成果。

下一动作：完成当前源码的双目标全量导出、完整 regression/quality、独立消费者任务与独立审查；之后推进组件不可变发布及 Root source-only 原生消费。
