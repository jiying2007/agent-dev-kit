# 负结果与边界

## 历史教训入口

只读审查阶段按规则用 `rtk rg` 检索 `knowledge/L2-domain/lessons.md` 的 Skill/trigger/reference/protocol/overflow 关键词，实际返回 exit 2：该文件不存在。此处无可复用历史条目，不补造经验，也不将缺文件当作本轮 Skill 方法失败。

## 原始失败路径

- F1：基线 7 条发布扫描中 6 条实际输出合成 secret 内容；仅既有专用 `-l` 扫描不泄漏该 sentinel。F2：显式子进程 130/143、自发 SIGINT/SIGTERM 后继续采样，产生后续目录并将最终状态折为 1。原始材料：`round3-optional-probes.json`；实施 RED 为 `round3-optional-red.json`，12 个测试中的 12 个预期 subtest failures，42 次真实命令。修复 GREEN 的对应调用完整保留，不将合成内容测试说成真实凭据审计。
- F3：旧 binaryDir 从 A 改 B 后 configure/build 均 exit 0、cache 指向 B，但生成系统配置、真实编译命令和程序仍为 A/101。`--clean-first` 后仍编译 A，排除仅残留对象文件的解释。原始材料：`round3-cmake-probe/{evidence,forced-rebuild-evidence}.json`。新方法控制修改前后均 4/4 pass；该“错误身份发生”是预期观测，不伪造测试 RED 或模型提升。
- F4：实际 5 schemas × 6 inputs 显示提前封闭 allOf 子 schema 会拒绝合法扩展，而 Draft7 忽略 `unevaluatedProperties` 会接纳未知字段。`round3-schema-composition-probe.json` 保留此语义反例；新增回归最初缺发布示例的失败只是验收资源缺失，不能替代语义反例。
- F5：两目标实际导出的空审核表共有 10 个无证据 `pass` 单元。`round3-checklist-probe.json` 和新回归保留实际表格；不用关键词存在测试冒充消费验证。

## 实施与集成负结果

- Core 初轮测试的链接正则跨越代码围栏，属于测试收集器错误；修正并保留第一次及后续原始回执，没有将它记为产品方法失败。
- Optional 初步 baseline 字节计算误用了会过滤输出的 `rtk git show`；数值废弃，最终身份用 `rtk bypass git show` 原始 bytes 重新计算。其他整合器使用 Python 子进程获取 Git 原始对象，并与固定 blob/SHA256 对账。
- 首次共享工作区 `large-refactor` 为 323771 / 323328 bytes，超 443 bytes；保留 Core `final-large-refactor-budget.json` 失败回执。通过既有 interface 说明等义去重收敛，禁止改预算阈值、删除能力或弱化约束。最终读数另见完整 profile 回执。
- 新 CMake 消费者第一次以裸 `rtk` 读取任务时 PATH 不含它，exit 127；补充现有真实二进制的绝对路径后继续，未更改任务目标或提供方案。该环境入口失败记录在消费者原始命令中。
- 互联网交叉核验中的 CMake v3.31 网页请求返回 502；固定 Kitware/CMake commit 的文档和实现快照已实际取得并核摘要，未依赖该失败网页内容。
- 外部 Aspire 初始 `LICENSE` 返回 404，改查实际存在的 `LICENSE.TXT`，两次结果均保留于 optional 来源记录。

## 证据边界

上述 scratch 文件名描述原始执行材料；最终随变更保留的等字节副本由 `evidence/retained-files.json` 映射。未来的完整回归、独立审查、CI 和发布结果应追加为新回执，不覆盖已有失败。未运行的 native runtime、父进程/进程组信号传播、目标 ABI、板端/HIL、M5 和现场资格继续保持未验证。
