# 设计

沿用现有 Skill、matcher、compiler 和验证入口。先做全量只读审查，再为确认问题设计最小修复；当前设计不预设必须新增能力或修改多少 Skill。

## 所有权与阶段

- embedded reviewer：20 个嵌入式方法 Skill 的独立首轮审查。
- workflow reviewer：25 个工程流程 Skill 的独立首轮审查。
- context/optional reviewer：20 个上下文及 optional Skill 的独立首轮审查。
- coordinator：需求/设计/任务、交叉契约与成本检查、源包装、证据和发布整合。
- 实现任务在确定反例与验收后分配；终审由没有参与该实现的新 reviewer 只读完成。

前三组的互斥清单从冻结 Manifest 派生，共 65 项，不以非递归目录 glob 代替。审查者先读取原始资产，不提供预期结论；复杂行为使用真实任务形式的独立消费观察。

## 变更与验证原则

优先替换或压缩既有指令，详细条件按需保留在已有 reference。仅当重复实现或确定性工具失败有证据时考虑代码改动。source bytes 与模型 Token、用户时间分别陈述；不提高 ratchet 以容纳改动。

源测试根据采用的反例和验收设计，保留首次失败及修复后结果。技术依据核对官方一手来源并固定适用条件；宿主缺工具或真实设备时记录 unavailable/not-run，不借模拟证据提升资格。

## 确认后的最小实现

- 触发修复复用现有 frontmatter 与可选 `implicit_context`，不新增分类器、语言黑名单或权限通道。review 同义词在现有 routing intent 维护。BSP 的真实梳理用限定的领域条件避免把通用“梳理”引入全局误选。公共 routing/trigger 测试由一个作者整合。
- 独立终审后的 U02 修正：连续的 OTA 动作白名单误拒绝三个旧基线有效请求。恢复肯定的 OTA 领域词，仅在 `implicit_context` eligibility 内处理已声明领域词构成的紧凑并列名单：首项被否定时，相邻 `或/和/与/及/、/and/or/nor` 连接项继承否定；新句、逗号/分号或新动作打断。不得改全局 action/mode/permission 的 polarity 或新增语义分类器。验证多项并列、肯定/否定混合、引用和真实 OTA 保留，原全局权限拒绝路径继续回归。
- 独立终审后的 U06 修正：补回实际已复现的 VxWorks 领域词，并保留域外销售、明确无 RTOS 与 RTOS 相邻任务对照；不穷举所有操作系统或提升显式调用权限。
- 完整回归后的 U02 修正：固定 60 场景集的 SSH 专用诊断被新增泛“诊断”全局意图抢占。通用诊断应在没有更具体领域意图时作为现有 systematic-debugging 的候选，保持 SSH/ADB/串口专用路由优先；不改变原场景的 expected owner、数据集或权限规则。
- task-package 保持 canonical schema 与 19 字段不变，修正文档映射和输入类型防护；结构错误返回 errors，不以新增字段/放宽校验使旧示例通过。检查现有调用点及相邻 prototype validator 的同类型边界。
- RTA 仅补足原公式的适用假设；不新建调度器/模型，不改变既有 tick 与 timer 方法。
- 纯导出不分发 ADK 管理源码；源码命令须有可核源码根，缺工具时产出有界分析/交接并如实标记未运行。composition 使用现有 core 和 optional catalog 查询，不新增扫描器。
- archive 的修复动词统一到只读修复计划与后续实施交接，hash 差异的可信原件/授权核验保持不变。人类派工信封与机器 JSON 分开，scope 等信息不丢弃。

唯一共享写入作者维护 `manifest.json`、`src/agent_dev_kit/intent_boundary.py`、`tests/test_skill_trigger_matrix.py` 和必要的现有测试入口；其他作者仅写其分配的 Skill/专属测试。正式 reviewer 不改实现。

## 发布与回滚

预期以 SemVer patch 交付，具体版本在包装时按主线核定。经过独立审查与受保护 PR 后，由 exact-main 自动发布链生成不可变 Release。Root 沿用已有 source-only 两路径事务，只更新 ADK Gitlink 与自动生成的 `reports/current-status.md`；原生 attestation 和 main CI 分别验证。回滚使用上一不可变版本及精确 Root 指针，不覆盖历史 tag/Release。
