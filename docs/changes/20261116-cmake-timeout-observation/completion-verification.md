# 源阶段收敛与交付入口

## 当前增量

本轮接续PR #278未完成交付；保留原故障命中/恢复和IMAP精确时间方法，进一步完成完整发件地址判定，以及CMake测试失败的有界诊断。仍为65个Skill，未新增生产客户端、依赖、Profile或放宽预算。

- 冻结基线：`643bb1e93d118bb36c322094b4d1b70078ce78c5`。
- canonical source：`fe5f908d821b8cf56db140d053134ae835127c57`。
- source tree：`eddbe93c5cc0202e2a29e95364197260e1d2464f`。
- 先前本地提交`5cef7a190806f8c8cc35762b35f3d5057d66a56d`与canonical相同parent/tree、不同commit metadata；不混称同一个commit。

## 实际验证

| 检查 | 结果与边界 |
| --- | --- |
| 最终方法聚合 | 200/200，0 skips，exit0；unittest15.746秒，编排16.037807秒 |
| strict | exit0，Validation passed，2.578392秒 |
| 原Profile预算 | 8/8；所有原阈值逐字保持，large-refactor总源码323320/323328 bytes |
| 独立Spec/Quality | PASS/PASS；2个具体finding已修复，未解决0；14个路径精确hash绑定 |
| 独立CMake与诊断 | 原ADC单例0.351秒通过；bounded/partial/unavailable控制均通过 |
| 独立IMAP | 8项通过；100/300层正常控制、600层解析失败隔离及前后成功项保留 |
| 最小上下文消费 | 新线程只读Skill和离线任务，正确返回匹配101/104、排除102/103/105、未判定106/107，partial |

本地聚合和strict在提交前工作树执行，其回执如实保留当时HEAD/status；当前源码另有逐文件绑定及独立审查。后续必须由受保护CI执行提交的精确SHA，不用本地结果冒充该CI。一次消费观察不建立A/B、任务完成率或Token/费用改善。

## 失败与修正保留

1. 原run43892815480 attempt1最后记录到CTest，attempt2最后记录到build，均超原15秒预算。两份connector解码日志原文保留于`evidence/integration-bundle.json`。历史根因仍unknown；后续一次通过也不反推修复。
2. 独立审查指出诊断扫描合法截断不应造成新失败；现仅完整observed快照要求child出现，原清理/隐私/非本组隔离断言保留。
3. 新test-owned IMAP方法控制曾在预算内的深层注释头上抛RecursionError，丢失成功项。现仅捕获明确解析失败，失败UID保持partial并继续；不调整递归上限、不冒充生产邮箱缺陷。
4. 初次独立CMake检查因PATH缺工具跳过；原skip保留，后续使用已发现真实工具才得到0.351秒执行通过。

旧`20261116-skill-observation-precision/review-evidence.json`及其证据保持原样，只证明其原冻结源。当前IMAP Skill和聚合入口已变化，旧“51引用匹配”不再作为当前结论；本轮`review-evidence.json`覆盖当前14路径及原始patch。

## 证据读取与后续状态

`evidence/integration-bundle.json`为gzip+base64封装，含uncompressed/gzip字节和SHA256；解码后逐条核对13个文件的bytes/sha256。原始patch、source-bindings、独立报告、原始probe/输出分别保存。摘要引用验证不等于外部运行态或产品授权。

源码准备、实际方法验证和独立源审查已完成。PR、main、不可变Release及Root接入以[PR #278](https://github.com/jiying2007/agent-dev-kit/pull/278)、对应Actions与Release、Root新PR的真实回执为动态交付入口；本文件冻结在提交之前，不预填未来成功。后续证据包装必须保持这14个源路径不变。

沿用已授权source-only边界：宿主`~/codex`不可用，Knowledge Provider/宿主Execution Policy未执行；native、真实邮箱、HIL、M5/现场资格均未获得。`software_m5_certified=false`和`release_authorized=false`不因组件发布改变。
