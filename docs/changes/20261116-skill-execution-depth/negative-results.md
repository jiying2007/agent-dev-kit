# 未通过与证据边界

## 既有发布超时

`v11.3.7` run `43798551346` attempt 1 / job `133073038045` 在 ADC CMake 用例的 configure 与四个构建步骤完成后，进入 CTest 时触发原 15 秒总工作预算。原诊断保留 `work_elapsed=15.002s`、两流与最后命令；没有足够证据判定是测试体、CTest 启动还是 runner 环境。

相同发布的 attempt 2 已成功。当前本地补齐 CMake 3.31.6 与 Ninja 工具后，基线的 5 个 Ninja/MultiConfig 用例实际通过（总外层 1.4033 秒）。这只关闭了当前环境缺工具的跳过，不证明历史超时根因已修复；预算、失败语义和用例均未改变。

## 第一轮容量检查

初次集成新方法后，原有 profile 源码体积限制拒绝 4 个 profile：embedded-fullstack 超 5,357 B、incident-response 超 3,008 B、large-refactor 超 5,765 B、release-hardening 超 638 B。入口较短仍不足以满足总源码上限。后续仅在本轮修改路径内整合新旧方法、删重复说明，不提高原阈值。逐项原始数据见 `evidence/profile-first-check.json`。

## 本轮中间错误

- 新增寄存器比较表达式最初遗漏外层括号；在 C 中 equality 比 bitwise AND 优先。真实 C 反例失败后改为完整括号，保留原表达式及编译/运行结果。这是本轮中间改动问题，不记成基线缺陷。
- 首个 FSMonitor 测试夹具误发重复 NUL，Git 自身报错；修正为官方协议后重新观察。无效夹具留存，不将它计入 ADK 缺陷或通过分母。
- 本地 Ninja wheel 准备首次假定 `ninja/data/bin/ninja` 路径，实际该 wheel 使用 `.data/scripts/ninja`；读取真实目录后按准确路径提取。准备失败时尚未执行 CMake 测试。
- 一个本地容量记录命令遗漏 `PYTHONPATH=src`，导入失败且未产生验证结果；补齐现有源码入口后才保存实际数据。
- 一次 37 项集成定向检查有 36 项通过、1 项因版本已同步而未执行的 A/B prereg 候选仍写 11.3.7 失败。只将 planned_release 更新为 11.3.8，并追加 11.3.7 零执行历史；分组、阈值和结果未改。该用例随后实际通过，未将未执行登记当成效果证据。
- 整合后 large-refactor 曾仍超出 27 B；仅在 performance Skill 压缩重复引用导语后为 323,263 / 323,328 B。独立审查修正版本号和协议约束后最终为 323,288 / 323,328 B，仍通过原门槛（余量 40 B）。

这些记录不建立模型效果、Token/费用、原生宿主、ARM 或板端/HIL 资格。

## 独立初审发现与修正

- 6 个已修改 Skill 的 frontmatter version 尚未提升；运行 bundle 使用 `skills/<name>/<version>` 路径，同版本新内容会造成身份歧义。本轮将这 6 项各升 patch，连同已升版的 register/protocol，8 项均有新版本；未重新执行外部 team-assets importer，不将历史导入拒绝算作本轮观察。
- protocol 压缩正文时丢失“各层独立 timeout/状态机”的明确约束。已恢复该约束，保持分阶段预算与操作总 deadline 同时成立。
