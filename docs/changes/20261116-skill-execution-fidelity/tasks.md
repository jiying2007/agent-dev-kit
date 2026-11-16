# 任务

前置设计：@docs/changes/20261116-skill-execution-fidelity/design.md。

| ID | 责任/写集 | 当前状态 | 验证 |
|---|---|---|---|
| T1 | 研究者：只读外部一手来源；领域审查者：65 Skill 覆盖 | 完成 | 65 入口 + 53 直接引用；固定原始来源、15 初判 fix/50 retain；最终修改 16 Skill，逐项见 audit |
| T2 | root：`matcher.py` / `_matcher_kernel.py` 与现有路由测试 | 完成 | 提升排除、精确名称拒绝与有限显示格式实际 RED→GREEN；独立 27 个路由检查通过 |
| T3 | 领域实现者：BSP、接口、branch-closeout Skill 与 `test_skill_command_examples.py` | 完成 | 19 项命令测试通过，含 7 个 GNU make 场景与真实 C 编译/11 组向量；授权只作语义检查 |
| T4 | root：设计探索 Skill 与现有内容/触发检查 | 完成 | 稳定 ID/来源/依赖失效；两个定性观察保留精简前后版本边界，不计控制模型 A/B |
| T5 | 评测实现者：任务评测 bounded context 与现有测试 | 完成 | 时间/组成 RED→GREEN；合同/schema 下一调用变化可见；同机 36 合成观测各三次计时 |
| T6 | root：源码版本、合同、验证证据；独立审核只读 | 完成（源码与本地证据） | strict/原预算通过；最终冻结 102/102，288.284 秒；独立 Spec/Quality PASS、116 项与 27 路由检查通过；typed 证据另按实际摘要校验 |
| T7 | root：受保护 PR、主线/Release 核验 | 阻塞：自动审批拒绝远端写入 | 两次 push 均被拒绝；不尝试替代写入。只读确认分支/PR 未创建，main 仍为基线、最新 Release v11.3.4 |
| T8 | root：现有含 rtk 的 Skill/直接引用与 `test_skill_content_contract.py` | 完成 | 65 项导出命令扫描；无 wrapper PATH 的 Review 命令实际执行；内部命令限定已核验 source root |

仅依据实际输出更新状态。需求/设计经 research_skill_methods 独立只读预审；新增 T3/T8 先修订合同。源码冻结为 `016d673331ef458ac94f72d08ec67537a000cc4b`，此后仅归档证据、审查与交付文件。真实模型 A/B、Token/成本和设备结果未测量。最终本地审查不能替代后续平台门禁或解除自动审批；远端阶段需本轮可接受的明确授权后继续。
