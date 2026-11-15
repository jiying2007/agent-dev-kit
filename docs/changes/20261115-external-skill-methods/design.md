# 设计、影响与验证边界

前置需求：@docs/changes/20261115-external-skill-methods/requirements.md。

## 采用方式

保持既有 Skill 与生产消费者边界，以六类任务方法补足实际缺口。普通任务不自动启用全部新步骤；入口说明何时需要，reference 提供具体动作、失败解释和最小证据。

| 方法 | 主要落点 | 条件与实现边界 |
|---|---|---|
| 兼容迁移 | `adk-task-breakdown` 的正文与 `vertical-slice-planning.md` | 仅普通纵向切片不能保持公共契约时使用；临时兼容有退出任务，不形成新的长期权威或自动真实迁移 |
| 独立 oracle | `adk-test-strategy` 的正文与 `high-value-tdd.md` | 从契约得出 expected；用明确错误变体验证断言敏感性，保持正确实现及合法输入 |
| checker 校准 | `high-value-tdd.md` 与 `adk-verification-before-completion` 的既有 reference | 新建/修改/可疑判定器才校准；业务结果、完整性与进程退出分开，复用同快照有效证据，不另造 Gate |
| property/stateful | `adk-unit-test-embedded` 正文及自身 `references/property-stateful-tests.md` | 性质必须独立、输入非空、操作可重放，区分边界枚举、性质框架和 coverage-guided fuzz；不引入框架依赖 |
| sanitizer | `adk-systematic-debugging` 正文及自身 `references/sanitizer-validation.md` | 先检查编译器/target/runtime 支持；以同构建负例证明工具有效，UBSan 报告不能凭 exit 0 忽略；unit/static 只做条件性 Skill 交接 |
| stack | `adk-performance-profiling-embedded` 正文及 `mcu-memory-footprint.md` | `.su` 逐函数信息与调用链、动态栈、IRQ/RTOS、实测余量分离；没有全边界时不宣称最坏上界 |

## 可携带性与上下文

`src/agent_dev_kit/targets.py::_render_main` 会按 target contract 重建 frontmatter，不能依赖作者自定义 `constraints` 等字段必然进入宿主；新增方法的必要边界保留在正文和真实可达的 reference。

`_render_support_files` 只携带已选 Skill 自身支持文件。`systematic-debugging` 出现在不含 unit 的 profile，static 也有独立组合，因此 sanitizer 完整方法归属于 systematic。跨 Skill 消费只指明按需交接与未安装边界，不增加必须存在的跨目录文件链接；单独导出仍自包含。若后续发现需要新的安装依赖，先重审设计，不能悄悄改 Manifest。

所有主入口与 profile 使用原有字节阈值，不靠上调预算通过；必要缩写只删除重复解释，保留工具类型、架构前提和失败处理。详细新增方法有实际价值才增加 reference，不制作统一空模板。

## 验证设计

- **迁移**：隔离真实 Python 包，两个消费者共享旧接口。直接移除旧接口和过早 contract 应失败；expand、逐个消费者迁移、最终 contract 保持相同外部结果。不是对用户工程执行迁移。
- **断言**：给出一个真实错误变体，证明复用被测 helper 生成 expected 会漏报，而独立常量/fixture 能拒绝；正确实现与边界输入通过。不用关键词命中替代这次程序执行。
- **checker**：隔离 scanner 进程返回真实结构与退出码，故意包含“exit 0 但违规/错误/未完成”的输入；最终示例的实际校准入口分别接受正常/阈值内和拒绝违规/错误/未知/缺覆盖。只演示判读方法，不新增生产 scanner。
- **property/stateful**：用标准库或当前已装工具运行有界合法/非法序列和边界输入，保存具体反例及重放结果，校验状态重置与非空覆盖。未使用 Hypothesis/libFuzzer 时明确不用其名义计执行。
- **sanitizer**：现有 host GCC 可运行的 UBSan 已知 signed-overflow 原例、默认 recover、禁止 recover 与修复例；其他检测器只有实际支持且执行后才能报通过，缺工具/运行时保持未运行。按工具官方文档核 flags。
- **stack**：GCC `-fstack-usage` 编译隔离 C 程序，区分真实 static frame、嵌套调用与 dynamic frame，证明 max(frame) 和 dynamic 行的固定数字不能直接作为任务栈上界；不对不同编译器数值写死断言。

两份独立测试模块接入已有 `tests/test_skill_content.sh`，不增加 full-suite 组数或新测试平台。默认不安装工具；可选工具缺失记录 skip/not-run 并保留真实覆盖数量。完整现有回归、strict、profile ratchet、质量与安全检查仍为必要验证。

## 来源、证据与发布

研究记录区分：检索发现、读取原文、固定版本、采纳方法、保留或拒绝；不把搜索缓存中的旧文件归入当前 commit。许可未确认或限制较强的来源只做独立方法概括，外部脚本不执行。源文件和测试先冻结验证，证据工件后补；完整待发布树再跑内容/敏感信息检查，避免旧轮 synthetic credential 形态进入公开日志。

独立 reviewer 只读审查合同、源码、反例和真实回执，并为准确源快照给 Spec/Quality 裁决；静态检查与 host 示例的证明范围不可扩张。所有 source-only 限制、失败和未测量项目保留。

候选版本 `11.3.4` 使用既有版本管理入口与 canonical release 流程；不改变受保护规则或发布机制。用户既有推送/合并授权继续有效。回滚为回退本轮提交，无安装、用户数据或设备状态迁移。
