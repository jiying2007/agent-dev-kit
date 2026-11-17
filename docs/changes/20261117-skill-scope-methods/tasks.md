# 任务

| ID | 任务 | 可执行 verify | 状态 |
|---|---|---|---|
| T1 | 收窄嵌入式单测隐式路由 | public matcher 领域外反例、MCU/host/Rust 正控与既有 route tests | implemented; targeted checks passed |
| T2 | 修正 7 项入口/参考的方法与范围 | 定向方法、真实 rg、两种 team-core production export；相关现有 tests | implemented; targeted checks passed |
| T3 | 整合并保持体积约束 | 8 个 enforce_profile_ratchet、strict validation、required regression | source checks complete; local full 101/102 FAIL retained, isolated repaired suite 204/204 PASS; exact CI pending |
| T4 | 独立复核与版本发布 | 原始只读 Spec/Quality 报告、受保护 PR CI、精确 main/Release 结果 | independent source Spec/Quality PASS; packaging review, protected CI and release pending |
| T5 | Root 接入与终态核验 | source-only promotion、Root 独立 review、PR/main required CI | read-only preparation complete; awaiting immutable release |
| T6 | 记录效果边界与复用入口 | Goal/loop/context 现有评测协议和实际观察分级，不虚报 usage/收益 | bounded continuation observation complete; general effect not measured |

## 当前状态

- coordinator 当前职责：设计与协调；实现按分工委派，审核单独只读执行。
- 基线：ADK 0973b9d / 11.3.12；Root 8b9c5ac。
- 教训检索：knowledge/L2-domain/lessons.md 不存在，已记录负结果；不生成虚假历史条目。
- T1/T2 实现已冻结；原始定向结果分别见 evidence/routing 与 evidence/methods。方法审查发现的 Low 测试盲点已收紧，并保存旧坏变体 GREEN、新五种坏变体 RED 和真实源码 GREEN。
- 独立近邻审查发现首次实现将行内格式化技术名误当引文删除：四条旧版成功请求退化为 abstain。首次完整回归因此中断（exit 130，不计通过）；补修保留正常行内技术名及否定极性，继续排除代码围栏和有限标记引入的示例引用。新增七条格式化正控先 RED 后 GREEN，原矩阵及新增项合计 21/21；完整回归必须重新绑定补修后的冻结提交。
- T6 见 evidence/continuation：实际当前任务的新上下文恢复观察，保留全部验收、owner、依赖和未完成状态；单次观察不证明通用改善、原生宿主效果、token 或成本收益。
- 第二次完整回归实际为 101/102；唯一失败是未执行评测计划的候选版本落后于 manifest。仅同步版本并保留 11.3.12 未执行历史后，完整失败 suite 的 204 项通过；原失败单项也经独立复验。未改的 101 套证据按精确树差异复用，未伪造新的本地完整通过。
- 独立源码审查目标为 66df0ce7092aabbbd05411ef2950cc9ee59a3592，三项发现均 fixed-and-independently-verified；原始报告与完整补丁随证据保存。
- 本表记录证据包装时状态。后续精确 PR/main CI、不可变 Release 及 Root 接入结果由对应 PR/运行回执与 Root 状态投影闭环，不能预填成功。
- 下一动作：证据包装增量复核；受保护 PR/main 全部所需 CI 通过后发布；核验不可变 Release 后执行 Root 两路径事务与独立复核。
