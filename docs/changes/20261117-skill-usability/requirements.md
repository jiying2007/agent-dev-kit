# 需求

用户在 v11.3.13 完成交付后要求继续全面优化所有 Skill 并落地。本轮目标是从当前源码找出新的、可支持的使用与方法缺陷，修复并完成源发布和 Root 消费闭环；不重复计算上一轮成果。

## 冻结范围

- ADK 基线：`78c3be7f6f9b5ee2e557de54156532fb3169198d`，版本 11.3.13；Root 基线：`5e29f690bce4118aca7f89f76cfb08713bb54f4a`。包装与合并前重新核对远端。
- 覆盖 Manifest 的 56 个 core 和 9 个 optional Skill，包含嵌套子项；保持 65 个身份和既有产品边界。
- 聚焦实际任务方法、触发/交接、导出可用性和上下文负担。只对有具体反例的缺陷实施最小修复，不为覆盖率修改所有文件。
- 保持 8 个 Profile 原源字节 ratchet，不增加 runtime、发布、设备权限，不改历史资格或虚构模型/设备/Token 测量。
- 提交、受保护 PR 合并、自动独立审查和发布沿用本会话授权；不启动额外付费模型任务或定时巡查。

## 验收

1. 65 项有逐项审查记录；发现和未发现、静态缺陷与实际失败分别记录。
2. 每项采用的修复绑定可复现反例、最小变更与正反验收。共享实现变化遵守完整回归要求。
3. 保留真实负结果，独立审查绑定最终源码与新验证；不以关键词测试代替真实工具行为。
4. 通过现有发布链生成精确源码对应的不可变组件 Release，并按 Root 已有 source-only 事务消费；验证实际 main CI 的原生证据。
5. 在最终结果中区分源码/发布、Root 消费、原生 runtime 与产品/设备资格。

## 已复现并采用的验收项

| ID | 当前反例 | 修复后的可观察条件 |
| --- | --- | --- |
| U01 | 中文“代码评审”选到提交/PR 检查 Skill | 普通 review 与局部意见核验选 review-loop；提交 PR 的真实意图保留，否定与只读边界不变 |
| U02 | Python 诊断、Web 超时与数据库回滚选到设备现场 readiness | 域外任务不选设备 Skill；真实嵌入式/OTA/产测任务及原适用正例保留；SSH 等专用意图优先，泛诊断可走既有 fallback，不提升模式或权限 |
| U03 | task-breakdown reference 列出的 5 个额外顶层字段被真实 v2 validator 拒绝 | 机器包使用现有 19 字段及跨字段规则；scope/接口/全局约束仍保留在合法字段或外层调度信封；两种导出均可理解该映射 |
| U04 | v2 的 artifacts=null/[1]、kind=[]、retention=[] 导致异常 | 错误 JSON 类型返回非空验证错误，不抛异常；有效 decision/research/prototype/implementation 与权限拒绝对照保留 |
| U05 | RTA 的严格高优先级求和漏算同优先级干扰 | 公式明确限于每任务优先级互异；同优先级轮转另选已验证模型，不把两任务各 C=6/T=D=10 的主机算术当可调度或板测 |
| U06 | 销售团队“任务设计”、无 RTOS 裸机任务被选为 RTOS 设计 | 保留真实 RTOS 上下文，域外或明确否定 RTOS 的任务不选该 Skill；显式诊断不提升权限 |
| U07 | 仓内 bsp-analysis-positive 原始提示在 matcher 中 abstain | 真实 BSP 代码梳理任务可选择现有 BSP analysis；域外“梳理”及 BSP 实现/高风险相邻任务不被错误吸收 |
| U08 | IRQ/DMA 排除短语中的 slash 使合法 CPU budget 场景被拒绝 | DMA coherency/IRQ 分析不因已满足 CPU 预算被排除；明确无需 IRQ/DMA 的纯轮询任务保持退出 |
| U09 | optional composition/security 在纯导出根调用未分发 devkit.sh；catalog 初始盘点仅56 core | ADK 源命令限定已核源码根；纯导出使用已存在的目标输入并明确未运行源码检查；源码盘点 core/optional 并集精确65 |
| U10 | archive Skill 写“修复”但 canonical effect 为 read-only，缺实施交接 | 本 Skill 只读定位、提出最小修复和验证交接；写入由原任务中已有授权的实施步骤执行，不放宽 effect ceiling，不凭文本自授权 |

同一路径的低风险澄清：parallel 的 Markdown 人类派工信封及 planning 的 v2 速记不能直接当 canonical JSON；保留 scope/owner/report 信息，按接收方合同映射。原始报告中未充分支持或仅一般同义词漏选的观察单列，不把所有 lexical matcher 限制当已确认缺陷。
