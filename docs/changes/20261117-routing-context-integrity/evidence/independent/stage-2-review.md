# 第二阶段独立审查（仍未最终冻结）

审查身份沿用 `independent-reviewer-routing-context-20261117`。本阶段没有修改产品源码或测试；仅写独立探针及内部审查证据。

## IR-1：fixed，已独立复验

原始六项数值探针在修复后重新执行。普通有限值通过；bool、NaN、单次 Infinity、`10**400`、两次 `1e308` 全部经 `ManifestError` 明确拒绝。
`_finite_nonnegative` 在既有准入模块进行精确类型检查、有限浮点转换、逐项校验及聚合后校验；有效零值和安全 False 没有被转成成功。
证据：`campaign-number-probes-reverified.json`。新增 runtime 成本兼容测试的目录归属仍由协调者/实施者处理，未将此已发现集成中间态隐藏。

## IR-2：major / open，worktree 常用修饰语穿过否定

下列输入均明确禁止新 worktree，但实际选择 `adk-worktree-governance` 并返回 `mutation_permission=workspace-write`：

- `不要创建新的 Git worktree，直接修复当前分支的代码`
- `不创建新工作树，直接修复当前分支的代码`
- `Don't create a git worktree; 直接修复当前分支`
- `Do not create any worktree; 直接修复当前分支`

原有限 filler 枚举未覆盖这些常见修饰，长创建词未匹配时 bare worktree/工作树仍成为肯定匹配，违背验收 2。
肯定控制：无关 `不要更新 ADR` 不应压制真实创建请求；前句禁止创建也不应压制后句新的明确肯定创建。

## IR-3：major / open，被解释/审查的动作不是执行请求

四个解释/概念/审查对象输入都被选择为 `adk-adr-writer`：

- `请解释编写 ADR 的方法`
- `只读解释“更新 ADR”这个术语与接口契约的关系`
- `请解释为什么更新 ADR 有助于接口契约追溯`
- `只读审查代码中的更新 ADR 实现`

更严重的同根因权限反例：`请解释如何实现 RTOS SPI DMA 驱动` 与 `请说明怎样实现一个 RTOS SPI 驱动`，都返回驱动实现能力并给出 `workspace-write`。这是解释请求，按验收 3 应保持 deny。

修复不能成为全局“解释”排除规则。以下当前正确的肯定控制必须保留：

- `请编写 ADR，解释接口契约的取舍`
- `解释 API设计 的风险，然后请更新 ADR`
- `不要解释如何编写 ADR，请直接编写 ADR`
- `请实现 RTOS SPI DMA 驱动，并解释设计取舍`
- `不要解释驱动原理；请实现 RTOS SPI DMA 驱动`

独立脚本 `probe_routing_boundaries.py`；依序保留 20、26、30 项原始结果。最后一次 `routing-boundary-probes-expanded-30.json` 为 20/30 符合预期，失败即上述 4 项 worktree 与 6 项被解释/审查的动作。

## Fresh 验证与来源检查

- phase context：19 tests pass。
- skill relationships：8 tests pass。
- campaign materializer：11 tests pass（在 runtime 成本兼容测试迁移前）。
- trigger matrix：29 tests pass。
- routing IR contract：5 tests pass。

上述原始日志分别保留在同目录的 `*-tests.txt`。测试通过不能推翻独立反例。

`source-integrity-probes.json` 另外证明：

- 审查清单正好覆盖基线 manifest 的 65 个身份与对应路径；54 个直接参考不重复，119 份原始文件 bytes/digest 与 Git 基线相符；每项有结论。
- 原 profile ratchet 文件、原 M5 固定任务数据完全未改。
- formatter 从内核归回 canonical matcher 后，AST 除函数名外与基线完全相同；全库调用点检索没有遗留依赖。
- 两个独立读后变更注入实验保持 size/mtime：phase 与 relationship 每次只读取 contract 一次，返回摘要匹配已解析旧 bytes，下一次读取拒绝已改变的无效内容。

## Context 方法冷读判断

已完整读取三个改动 Skill 及其 diff。新方法要求先核当前目标和权限，再判断 active Skill 的来源、内容身份、必要 refs 与正文状态。

| 独立场景 | 依正文作出的决策 |
| --- | --- |
| 同来源同内容，完整正文和当前所需参考仍在上下文 | 可去重，保留当前权限与原始证据入口 |
| handoff 留有“曾加载”记录，但正文仅余摘要或已经丢失 | 重读当前任务仍需要的 Skill 与必要参考；历史加载记录不能代替当前内容 |
| 来源或内容已经变化，旧正文仍在 | 按当前目标重核并读适用来源；未知版本/hash 明示，不能伪造身份 |
| 历史 Skill 已与当前目标无关，或必要来源不可读 | 前者留在 excluded；后者报告 needs-evidence / needs-fix，不能扩大权限或宣称恢复完成 |

该判断仅为审查者按所给方法进行的冷读应用，不是宿主自动 context manager、原生 runtime 恢复、模型 A/B 或 Token/费用效果证据。压缩后 manual approval、raw fallback、高风险证据、memory candidate 与过期目标排除边界仍保留。

最终状态：等待 IR-2/IR-3 修复、runtime 测试归属集成、最终精确源码提交和完整回归。当前不得生成 canonical Spec/Quality pass。
