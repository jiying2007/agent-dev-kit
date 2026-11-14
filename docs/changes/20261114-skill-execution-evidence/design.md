# 设计

## 基线

候选基线 PR #264 HEAD `868894fbde3268381276c3557704af8ba6d569d7`，
主线 `7aed1d2545babce16c41dc021ead01c8c324ce07`；先由独立审查者核验现有 PR。
当前角色：协调/设计。实现者负责源码与定向测试；独立审查者只读，不能自审认证。

## 边界与数据流

已授权宿主产生任务观测包 -> 有界只读导入 -> TraceRunFacts -> RunEvidence -> 现有 compare-trials。
导入包显式包含运行身份、完整性声明、原始轨迹/验收/产物的相对路径和摘要。
原始工具记录与实际暴露、验收材料一致性由导入器核查；保留 caller-observed/test-only
信任边界，不把本地摘要校验声称为原生宿主认证。最终产物验收与工具权限检查分别记录。

新增能力放在 `src/agent_dev_kit/` 的单一 task-evidence bounded context，
通过现有 `evaluation_cli.py` 增加非执行入口。使用既有 schema/Run Evidence，
输入格式若需新 schema，只定义本导入边界；不复制 trace summary 或统计协议。
输入使用 strict JSON、有界文件读取、无网络/命令执行、路径穿越及符号链接拒绝。
raw 内容不进入输出，现有 evidence_ref 指向已核验内容摘要。

实现核对发现：既有 compare-trials 仅核对其原有 plan/control 与 runtime 身份，
并不解释任务导入新增的 input/workspace/exposure 引用。因此增加最小的
`compare-task-trials` 前置组装边界，读取固定任务身份与本地观测引用、逐份调用导入、
核对冻结 source/Skill 内容/input/workspace/grader/provenance 后交给原统计器。
不改变既有通用 comparator，不复制统计算法。若单模块接近现有30KB预算，
配对逻辑放入业务模块 `task_trials.py`，不产生泛化 support 模块。
单份导入报告明确 `pairing_authority=none-single-observation`。
按既定分组保留未触发与任务超时的试验；真实加载事实另列，不能以“未加载”筛掉差结果。
no-skill 侧实际加载目标 Skill 属对照污染；来源/初始状态漂移是 invalid，并保留错误原因。
所有 CLI 输出在写入前检查，不覆盖输入、计划或已读引用文件，也不跟随输出符号链接。

成功从验收材料生成。原始观察缺失、计量不全、模型身份不确定分别保留状态，
任何固定零值不得补足观测。统计器继续负责完整试验、成对控制变量和判定；
导入 API 不拥有 promotion/release 权限。现有 routing materializer 保持原样。

## Skills 与基准

入口保留最小执行流程，详细规则复用既有 references；守住现有入口长度预算。
已有正确内容不改写。各工作包以真实失效类型和可验收任务为落点，
复用现有测试 runner。8 类开发案例包含修复、Review误报、恢复、KWS资产复用、
交叉编译、定向文档、明确/模糊意图、Optional缺失/否定，标记 source-only/development。
独立最终 holdout 在候选和执行环境冻结后产生，不借用开发 fixture 冒充。

## 兼容与回退

现有 CLI、Run Evidence、trace schema 和 effect comparison 的行为保持兼容。
新增非执行导入为可选入口；回退本变更即可移除新增能力。
若实现发现必须修改已有公共语义，先记录设计差异并做调用点搜索。
