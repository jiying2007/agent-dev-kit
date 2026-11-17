# 当前状态与任务

阶段：Spark / Design / Build 完成；三组已覆盖全部 65 项。OTA/VxWorks/SSH owner 三个回归均已修复，最终 102/102 套件通过。精确 source 的独立 Spec/Quality 均 pass，canonical 记录已由真实仓库 validator 接受；当前仅证据包装等待独立增量核验。组件发布和 Root 消费属于后置交付。

| 任务 | 状态 | verify / 证据 |
| --- | --- | --- |
| T1 冻结当前源码、恢复验证环境并分组全部 Skill | 完成 | 新 checkout HEAD 为 78c3be7；Manifest 56 core + 9 optional；分组 20 + 25 + 20 |
| T2 独立审查 65 项并选择具体反例 | 完成 | baseline 20 + 25 + 20；context/optional 初次导出覆盖概括的更正单独追加，不覆盖原始记录 |
| T3a 嵌入式适用条件与触发边界（U05–U08） | 实现及自测完成 | 互异/同级 RTA、BSP/SoC 正例、RTOS 域外与 IRQ/DMA 正反例 |
| T3b review/设备路由与机器交接（U01–U04） | 实现及自测完成 | 真实 matcher；canonical 19 字段 validator 接收与错误类型拒绝；两个实际 compiler 输出 |
| T3c 导出依赖、完整盘点、只读到实施交接（U09–U10） | 实现及自测完成 | helper 缺席边界、65 项 catalog 并集、只读交接和人类信封映射；原 8 个预算未抬限 |
| T4 整合验证与独立 Spec/Quality 审查 | source 双 PASS；包装独审中 | source a2b90b6；canonical review d58c843e…；102/102、双目标各65+54、8 ratchet；原中断、101/102失败与最终绿灯分别保留 |
| T5 完成组件 PR、main CI 和不可变 Release | 待 T4 | 精确源身份、发布档案、原生证明 |
| T6 Root source-only 接入和实际 main CI 核验 | 待 T5 | 两路径差异、原生消费及签名 CI 收据 |

恢复入口：先读本文件，再读 T2 的原始审查证据；上一轮结论见 `docs/changes/20261117-skill-scope-methods/`，已修内容不重复计入新成果。

下一动作：完成独立审查记录及仅证据包装差异的复核；随后推进组件受保护 PR、exact-main CI、不可变发布及 Root source-only 原生消费。发布后置事实以对应 PR 的 closeout 记录和真实 CI/Release 原始证据核对，不把本提交里的未来步骤预写为完成。
