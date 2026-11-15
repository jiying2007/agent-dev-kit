# 外部方法增量：实现中只读预审

- Reviewer：`external_independent_review`，未修改仓库实现。
- 基线：`5e0e83bcc127665de9a352e9eacfe9b092106cb2`。
- 范围：七个 Skill 的正文/参考增量、三个 core 公开程序及其测试、跨 Skill 文件依赖、新增触发词。
- 状态：**预审发现，不是最终 Spec/Quality；源码仍在作者修改中。**
- 具体重大问题：1 组（3 条已复现的新增触发误匹配）；最终结论待冻结源码和完整回执。

## M1：新增泛化触发词扩大到了明确不适用的任务

在 2026-11-15T14:09:59.292518Z 至 14:10:00.686474Z 的独立观察中，下面三个文件的 SHA256 在前后读取之间保持不变：

| 文件 | 观察时 SHA256 |
|---|---|
| skills/adk-unit-test-embedded/SKILL.md | `71619e6a214c76591cf2302d452e9d64a65aedfcff7b4445d75c2b9f704ec5d0` |
| skills/adk-systematic-debugging/SKILL.md | `b97b861390c0b64e57c51431dd4f0b1d941f41ec4a55d79971688b3f89d75b6d` |
| skills/adk-performance-profiling-embedded/SKILL.md | `926a230935c8664f89b97f2435341946aac0620f5aa99032fa65701f353be18d` |

cwd：`/workspace/scratch/771b38332ec2/agent-dev-kit-external`。执行的是生产 matcher 的真实 CLI，没有替换 matcher：

| Skill / 输入 | 观察结果 | 问题 |
|---|---|---|
| `adk-unit-test-embedded` / `为 Python Web API 编写性质测试，不涉及 MCU 或 RTOS` | exit 0，`match=true`，`phrase=性质测试`，primary/diagnostic-execution | 新增泛化词使明确非 MCU/RTOS 输入匹配嵌入式 Skill；未由领域限制排除。 |
| `adk-systematic-debugging` / `只解释 sanitizer 的基本概念，不排障、不运行工具` | exit 0，`match=true`，`phrase=sanitizer`，primary/diagnostic-execution | 单纯概念解释被选择为根因诊断主技能。 |
| `adk-performance-profiling-embedded` / `仅讲解数学上的调用栈上界定义，不开展任何基准任务` | exit 0，`match=true`，`phrase=栈上界`，primary/diagnostic-execution | 没有嵌入式指标/负载的定义说明被选择为性能分析主技能。 |

命令统一为 `bash scripts/devkit.sh match --skill <上述 Skill> --text '<上述输入>'`。所有真实 argv、cwd、stdout、stderr、退出码、源全文、前后摘要与时间均保存在同目录的 `external-methods-prereview-routing-observations.json`。

阴性对照：`adk-systematic-debugging` 输入 `当前调优不需要 UBSan，请仅说明算法复杂度` 返回 exit 1 / `match=false`。因此此发现不宣称所有否定都失效，也不把字符串 matcher 的结果扩大为真实宿主行为。

### 可执行修复与复验要求

收窄新增触发词或给出可信的任务/领域拒绝边界；保留真正诊断或嵌入式任务的正例，同时增加上述非领域、只解释与显式否定的生产 matcher 回归。优先在本轮 Skill/fixture 范围修复，不修改 matcher 或弱化既有测试来接受误匹配。root 已接收并分派该项；**本记录不声明已修复**。

## 其他已核事项与范围

- core 三个程序由 `tests/test_external_core_methods.py` 从实际 `render_asset` 导出的 reference 提取执行，检查本地迁移双消费者、独立 oracle 与 checker 判读。没有发现“测试另写一段正确 toy 程序而公开示例未执行”的问题。
- 实际运行 `PYTHONPATH=src python3 -m unittest tests.test_external_core_methods -v`：7 tests / 2.221s / OK。这里只记录预审时执行结果，不作为之后变化的最终源码验证。
- verification 的详细字段仍在正文/所属 reference；生命周期 owner/state/event/resource/termination/invariant、whole-lifecycle、高风险未查范围、权限 allow/deny 和真实证据边界仍可达。未发现因这次精简丢失必须字段的具体阻塞。
- 新 sanitizer 方法归 systematic 自身 reference；unit/static 只条件性交接，并说明未安装或 runtime 不支持时的缺口。未发现新增硬跨目录依赖。
- property 示例按长度枚举并将“最短”限定在其有限字母表；stack 明确示例只运行 host GCC x86-64，未验证 dynamic,bounded/IRQ/high-water；sanitizer 保留 ASan/TSan 未运行边界。域侧测试在观察时尚未提供，不给完成结论。

最终审查仍须核 domain 模块、修复后的触发回归、profile ratchet、冻结树全量验证、来源与证据的适用范围；本报告不替代这些验证。
