# 最终证据包装增量独立复核

**包装 Spec：PASS；包装 Quality：PASS。** 没有发现此次13文件包装范围内的未关闭问题。本附录仅确认该精确增量的完整性、引用和状态表述，不重新签署或改写原source记录，也不代表整个候选已经通过CI。

| 身份 | 值 |
|---|---|
| 原source base | `66df0ce7092aabbbd05411ef2950cc9ee59a3592` |
| 可追溯包装 target | `da34b8bed95d164eaab8982b0e13de508054ecfc` |
| 同内容本地包装 commit | `364515193669d33998f6f33660a756bd5af3d33d` |
| 两者完整 tree | `244034f7dd12265706842def554d9179ac7ce4a6` |
| 包装完整binary diff SHA256 | `8837f6b084d9e38eb46a89181867292cb19c60765c5f8b639991bff2c30f7991` |
| 最终复核时间 | `2026-11-17T02:55:09.452272+00:00` |

主审查实际字节/状态核验于 `2026-11-17T02:50:52.508172+00:00` 至 `2026-11-17T02:50:53.167223+00:00` 完成；子审查者的35项bundle核验完成于 `2026-11-17T02:53:04.252989+00:00`。主检查时工作区clean；以上结论绑定不可变commit，不将随后开始的源修复当作该已审包装的一部分。

## 已实际核对

- `66df0ce → 36451519` 及已fetch的 `66df0ce → da34b8be` 完整diff逐字相同，只有13个本change下的证据/任务/验证文件；生产源码、测试、版本和全局Harness记录均无变化。
- 原独立source报告JSON、Markdown和完整原patch与审查目录原件逐字节一致。原patch仍为 `7ce4b25c24f399c92998b405acd57f25fb192282173bd436bab57e52bea0030a`；没有重新签署不同内容。
- `independent-evidence-bundle.json`中的35条与原报告列举的路径集合完全相同，内嵌内容的原始字节、SHA256及bytes逐项相等，无遗漏或替换。bundle SHA256为 `f74152496716ccb79f9655ff4e1a2abb0f4de4cc8a4a871b58b75fb61ad57e51`。
- canonical review的scope、source target、审核时间、两个PASS和三项fixed发现与原报告一致；原limitations完整保留，仅增加tasks历史/包装增量说明。已独立调用既有`validate_review`，实际PASS，record SHA256为 `36b722287468397036087e15573520b952c620c0ef28f2e55df711e2ffe27f00`。
- `source-bindings.json`全部80项对照source66df的真实Git blob核对通过。当前tasks与原tasks的hash确实不同；原hash保留在原始报告、source snapshot及完整patch，canonical当前repository sources不再把旧tasks hash投影成当前文件。
- regression bundle的receipt、timing及stdout/stderr与原始r2证据一致，明确保持**101/102、exit1、FAIL**。204项修复suite的回执保持原字节，未伪装为新完整102项PASS。
- 体积摘要重新按基线及source对象计算：8入口净-216B，含2个reference共净-71B；八项ratchet与先前独立实际结果相同，无Token或模型效果主张。
- tasks和verification是包装时状态快照：exact CI、不可变Release、Root接入未填成功，Root明确以真实可核Release为前置条件。本附录解除该快照中的“包装复核pending”事项，不需要循环修改已签source记录。

## 新CI问题与后续边界

协调者在包装复核期间另报告平台workflow `44005719346` / job `133780475196` 失败：portable-skills audit将`implicit_context`识别为未知内部frontmatter。该问题暂记R-02，正在由原实现者做独立source增量；**不被本包装PASS涵盖**。原source/canonical报告保持历史原样，后续按`da34b8be → 修复精确commit`另做源码复核。

因此，本附录没有声明当前整个候选可合并或发布。精确CI、Release和Root接入仍需真实结果；没有新的全局Harness审批，也没有native/runtime/product或实际模型收益认证。未做新网络/设备操作，未修改仓库工作树、index或refs。只读检索的一次不存在文件诊断及更正记录另见packaging-increment-negative-results.md，不影响实际canonical validator的通过结果。

机器版附录包含13个实际变更文件的SHA256及各项原始核验依据。可以在PR正文引用本附录与其摘要；它不改变原source审查的hash或时间。
