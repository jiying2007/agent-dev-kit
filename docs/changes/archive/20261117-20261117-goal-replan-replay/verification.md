# C2 源码验证

## 验收映射

| 验证 | 实际证据与边界 |
|---|---|
| VERIFY-001：历史重放拒绝 | 原独立 A→B→A 冻结输入及 probe 原 SHA不变；原before exit1，修复后有/无verifier均由reducer拒绝 |
| VERIFY-002：合法流程保持 | 新C仍接受，exact event幂等、冲突/错Goal/错摘要拒绝、无intake兼容及implementation floor保持；execution policy25、相关Goal40、convergence9通过 |
| VERIFY-003：native trust失败不升级 | 同一合法synthetic receipt的false、exception、1/string/mapping全部拒绝；前后True正控制通过。生产trust代码原本正确，未修改 |
| VERIFY-004：独立与整体复核 | independent_review原样复跑冻结反例4/4并核定向测试；最终洁净候选完整回归102/102、exit0；1082个运行源输入不变，见相邻task-diagnostics/evidence/final，原失败轮保留 |

原始反例保存在 evidence/original-counterexample；实现者真实RED/GREEN、退出码、时间与diff保存在 evidence/implementation-observations.json。独立review记录独立生成，不从实现者PASS推导。

修复仅在同一次完整事件历史归约中追踪已消费attestation，无跨截断历史的新总账、schema或运行权限权威。实际来源事件准入、撤销、worker lease、外部commit/ACK和no-replay仍需真正宿主验证；默认无verifier路径本就保守，不能宣称真实宿主已被绕过或现在已认证。外部源码发行与Root晋级以真实后续回执完成。

回退仅通过正常后继源码变更及受保护PR；回退此补丁会重新暴露已记录的完整历史重放缺口，须明确保留该负面结论。既有版本tag、不可变资产和冻结反例不可改写。
