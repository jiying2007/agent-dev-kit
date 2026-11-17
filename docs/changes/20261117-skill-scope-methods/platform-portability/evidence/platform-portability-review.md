# R-02 平台可移植性登记增量独立审查

**Spec：PASS；Quality：PASS。R-02 已修复并独立复验，无未关闭发现。** 结论仅覆盖两个新增变更文件：平台内部扩展字段登记及既有平台suite的回归断言；原source/canonical报告和包装附录均保持历史原样。

| 身份 | 值 |
|---|---|
| Base | `da34b8bed95d164eaab8982b0e13de508054ecfc` |
| Canonical source target | `3568327a9877e2e789e079c6251cdf26af3c10c0` |
| 同内容本地候选 | `da32fcea0249120fa9828f22bf0add7bdf4f744b` |
| 完整 tree | `0f248f25597d33165b775e05ece5f8f6813a8103` |
| 原始增量 binary diff SHA256 | `76ccd29706ce6bd7f6a577ab450791dda37858dd172d4b2128c3968344b4c27c` |
| evidence_completed_at | `2026-11-17T03:01:28.174043+00:00` |
| reviewed_at | `2026-11-17T03:01:28.174051+00:00` |

实际已读canonical Git对象，确认其parent为base，本地/远端完整tree和增量diff字节一致，且仅改两文件。检查前后工作区clean；所有shell经指定rtk，导出与反例仅在独立审查scratch，没有写被审工作树、index或refs。

## 问题与最小修复

平台CI原始job日志显示`test_agent_platform.sh`阶段以exit1结束，日志未打印内部portable-skills详细JSON。独立审查者使用Git中旧平台合同、完全相同的65个Skill和未改变的公开audit实现，实际复现唯一错误：`adk-unit-test-embedded: unknown internal frontmatter ['implicit_context']`。因此原因有独立本地反例支持，不依赖对CI省略输出的猜测。

修复仅将`implicit_context`加入既有`portable_skill.internal_extension_fields`。从新JSON删除该项后，完整合同结构与base相等；`standard_top_level_fields`及其余所有字段均未改变。该字段继续是ADK内部路由元数据，没有变成portable标准字段，也没有降低未知字段的拒绝策略。

消费点审查确认，`portable_skill_audit`仍用standard与internal的精确集合识别已知键；其余键继续产生unknown错误。目标导出使用target contract重新构造frontmatter，preserve字段仍为license/compatibility，platform内部登记列表没有成为export白名单。路由权限、Fit Gate、native/runtime/product资格没有变化。

## 测试区分力与实际验证

新增断言同时保护“已登记为internal”和“未登记为standard”。未知键负例来自真实unit Skill，注入明确未登记的键，并要求fail状态及唯一、精确的unknown诊断；若实现忽略未知键、误拒已知字段或fixture注入失败，断言都会失败。子审查者独立阅读真实diff、consumer、两个target contract和既有export测试，未发现测试弱化或绕过边界。

| 独立实际检查 | 结果 |
|---|---|
| 完整`bash tests/test_agent_platform.sh` | exit0，平台原成功路径及新增拒绝断言通过 |
| 旧合同 + 同一65项源码/同一consumer | FAIL，唯一原因是未登记的implicit_context |
| 修复合同 + 同一65项源码 | PASS，65/65、failures=[] |
| scratch真实Skill注入独立键review_unknown_context_key | 按预期FAIL，唯一诊断精确对应未知键 |
| scratch还原真实Skill | PASS |
| claude-code实际release-hardening导出 | PASS，unit顶层仅description/metadata/name，无implicit_context，MCU/RTOS与host描述保留 |
| opencode实际release-hardening导出 | 同上，PASS |

上述baseline对照没有被冒称成新的完整基线checkout或102项suite运行；原合同来自base Git blob，consumer与Skill字节在两版本间完全相同。完整平台suite回执和各项结果分别保存在`raw/platform-frozen-suite.*`、`raw/platform-portability-controls.result.json`。原始失败job日志已保留为`raw/platform-original-ci-job.txt`，SHA256为`665dd9ec3fdf61f6ec531242f8a4abd29c4ec2274b60c2170ae84f36bdb8d69d`。

## 源码与证据摘要

| 变更文件 | SHA256 |
|---|---|
| `manifests/agent_platform_contracts.json` | `6c06ba6024ac53abaa82bff9fbf38e50cff38345f648db30fa216b4d083cef1b` |
| `tests/test_agent_platform.sh` | `4aad6a274453c669e12dab66d11ac53818542dd2806f8dd16e0fb5a60ccc0a44` |

机器报告还包含audit/CLI/renderer、两个target合同、unit Skill和既有export测试的实际读取摘要及范围。完整增量patch位于raw/platform-portability.patch，hash与上表target绑定。

## 限制与后续

本报告不重写原source审查、canonical记录、已保留的101/102本地失败或平台CI失败。它是以da34为base、356为target的独立增量结论。此前主CI某些job通过不能替代最终精确head的全部所需CI。

本审查没有新增本地完整102项运行，也未核验最终head的远端CI全部完成。最终CI、不可变Release和Root source-only接入仍需各自真实结果。静态导出不证明宿主discovery/load/trigger或模型效果；没有设备、真实网络客户端、付费模型、runtime/product晋级或新全局Harness审批。本结论不预先批准未来未读取的源码或包装变化。
