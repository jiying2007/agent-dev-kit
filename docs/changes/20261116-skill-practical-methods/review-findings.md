# 复核发现与闭合证据

正式独立源码裁决以 `evidence/independent-final-source.json` 和 `review-evidence.json` 为准。以下保留实现期间实际发现、失败尝试和修复，不能用无发现或机械绿色代替独立判断。

| 发现 | 处理 | 对应原始证据 |
|---|---|---|
| working-tree / clean branch / mixed 目标未进入 cached patch | 目标分流和明确端点；overlay、untracked 与缺基线单独处理 | general/results.json、general-implementation/red.json、green-index-refresh.json；独立导出执行 |
| Git stat-only 自动刷新 index | optional-lock 参数单独使用仍失败；局部禁用 diff.autoRefreshIndex 后通过 | general-implementation/red-stat-only.json、green-stat-only-final.json（真实失败）、index-refresh-experiment.json |
| 消费端隐含 ADK 源仓资源依赖 | 默认正文自足；核源码根与可读性后可选辅助资源 | 两 target 实际 export 与独立 T2 回执 |
| ADC 大输入乘法溢出 | 运算前拓宽、编译期整数合同、独立边界预期及 C11 构建接线 | practical-implementation/adc-native-red.json / adc-native-green.json；独立分开编译/链接 |
| review 入口压缩遗漏原 SOP 七个字段标识 | 恢复实际紧凑字段块，不改测试；重新冻结并跑完整入口 | attempt1/full-receipt.json；sop-contract-fix/green-sop.json；最新 full-receipt.json |
| 协议“延后”可能被误读为延长耗尽时限 | 明确先结束本轮，业务延后不复活原期限 | research/root-method-review.md；最终源码 |
| flaky 旧流程无条件隔离 | 改为按需隔离、核边界并保留原失败状态 | research/root-method-review.md；最终源码 |

CMake 的目录/configuration 方法和五个真实 fixture 已实现并通过源码审查前置检查，但本机缺工具；真实运行仍是平台资格门。缺工具拒绝实验的 exit 1 是预期的能力拒绝，不是构建成功，也不能据此给 merge/release readiness。

研究、作者 RED/GREEN、独立审查、完整源码回归和平台发布分别留存。文件名包含 green 的旧记录仍以实际退出码及对应源码摘要解释；最终 freeze 与回执有唯一明确入口。
