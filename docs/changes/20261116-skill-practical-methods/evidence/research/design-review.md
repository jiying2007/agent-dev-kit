# ADK practical-methods 独立设计预审

## 身份、快照与裁决

- Reviewer：`/root/external_skill_scan_v2`，独立 AI 设计/后续源码审核者；受 `/root` 明确委派。
- 范围：只读预审本轮 requirements/design/tasks 与对应基线源码、现有测试入口、导出依赖和预算约束。此前提供过外部方法研究；未编写本轮需求、设计、实现或回归测试，不代替后续独立源码审查。
- 工作树：`/workspace/scratch/2d6ca6dc3d38/adk-practical`。
- 已直接核对 HEAD：`5b88ec5bce351f68d4756d765e69a4f40bde3f07`。PR #270/main/Release 状态未由本审核者远端核验；本预审不声称它们已完成。
- 审核时间：2026-11-16T00:45:42Z（本地 UTC 时钟）。
- Spec verdict：**pass — design only**。
- Quality verdict：**pass — design only**。
- Blocker：**0**；Major：**0**。下列 A1–A4 为落实建议和最终证据检查点，不阻止按现设计进入已分配实现任务。
- Implementation / mechanical gates：**not-run / pending**；此裁决不是源码正确性、CMake 实跑、完整回归、发布或实际模型效果通过。

本次预审的确切文档 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `docs/changes/20261116-skill-practical-methods/requirements.md` | `2242052b60589fcf1dfa427dcd9371624b0d2208b124593ba2127a5692a46ed8` |
| `docs/changes/20261116-skill-practical-methods/design.md` | `0792361ccb247f13269db2c9791433d2d5718a94dee4a55728ad37a202855aef` |
| `docs/changes/20261116-skill-practical-methods/tasks.md` | `ecb3acbcaa9a89f0eadef73898e38c4ecfc22aa38f85ee348a205cf1fb1f7fbb` |

## 需求与当前差距核对

| 范围 | 直接读取的当前证据 | 设计判断 |
|---|---|---|
| Review diff 端点 | review evidence reference 只输出 `git diff --cached` 的 patch；`git diff --check` 不提供 unstaged patch；现有导出测试只在空初始提交核命令 exit 0 | 选择明确目标后检查实际 patch 内容是必要增量；四种 Git 状态比继续只查命令可执行性更有效 |
| context/handoff 随包可用性 | context-engineering Workflow 直接要求 `schemas/agent-handoff-v1.schema.json`；handoff 引用仓库级 `templates/context/continuity-attestation.md`；两者已有正文目标、状态、证据和下一步信息 | 默认正文自足、源仓辅助文件条件使用是最小修正；无须另建 schema 副本或新 runtime |
| ADC 整数计算 | `examples/embedded-test-matrix/src/adc_scale.c` 在 `int` 中执行 `raw * reference_mv`；原 C 测试只有 zero/full-scale/invalid 三项；现有 shell example 测试只检查文件与字符串 | 乘法前拓宽、明确整数支持范围、用满量程/钳位/无效输入独立性质验证有明确问题依据；接入已有 command-example 测试合适 |
| 堆测量工具 | performance Skill 明确写“堆用 memcheck”，已有有效负载、ABAB、采样扰动等规则 | 只修正工具/指标映射足够，不需重写性能流程 |
| flaky 同进程污染 | optional reference 的独立命令重复不会自动保留 suite 前序状态；unit-test 的隔离规则已存在 | 在有 suite/独跑差异时补充同进程顺序诊断是方法增量；按需 reference 放置符合范围 |
| 协议整体期限 | 已有分层 timeout、产品预算、次数与非幂等 UNKNOWN 对账；未给出剩余预算传播和 SDK/调用层重复重试关系 | 补足操作期限、退避计时与重试责任，同时保留协议时序、长连接寿命、跨主机时钟边界，设计合理 |
| CMake 构建目录/configuration | 当前连续列出手工 `-B build/<target>`、`--preset`、再回固定目录 build/test/ELF，不能保证同一个实际构建；未表达 configuration 绑定 | preset/manual 互斥且绑定真实 binaryDir/configuration 是必要修正；真实 CMake fixture 能验证文案对应行为 |

本审核读取的是上述 7 个 Skill/相关 reference 与 ADC 示例、关联测试、根 AGENTS/详细规则及 CI 回归入口。上一轮 65 Skill 的覆盖清单可以作为历史基线复用；不得将本次局部预审重新记成独立完成了新一轮 65 项逐项审查。

## A1：CMake 的工具缺口必须和验收结果分开

已独立执行本机工具发现：`cc=/usr/bin/cc`、`gcc=/usr/bin/gcc`；`cmake`、`ninja`、`clang`、`rtk` 均未找到。没有下载或安装工具。

要求 7 和 T4 已正确说明本地静态反例不算真实构建。最终证据应至少包含一个具备相应版本/生成器的执行环境中 configure→build→CTest→artifact 的实际输出，能确认不同 configure/build/test preset 名称仍落到同一 binaryDir/configuration。

- 本地缺工具可记录 skip；skip 只说明能力缺口，不满足“真实 CMake fixture 已核验”的验收。
- CI 总 job 变绿也不能单独证明该用例执行；检查具体测试计数、skip 原因与实际命令输出。
- 当前 regression CI 在 Ubuntu runner 安装 ripgrep/shellcheck 并运行 `tests/run_all.sh`，没有显式安装或核实 CMake/Ninja。不能只靠 runner 标签推断工具可用。若 runner 也缺工具，应保持该项未完成并由 root 在现有授权范围补齐已有验证入口，不提高预算或调用外部模型。
- 测试应运行实际发布的 Skill 命令块或直接由它参数化，不另写一套“正确的 CMake 命令”然后宣称发布文案已验证。configuration 变化应体现在产物/测试行为中，避免同一个缓存二进制使错目录用例假绿。

这是原验收的执行检查点，不要求新增顶层工作流或测试编排。

## A2：ADC 的整数支持合同与验证能力要对齐

设计提出“编译期约束声明可安全支持的 int 宽度”是合理的，落地时需写清支持的值域/整数宽度并与构建语言标准相容。核心证明是校验/钳位后乘数均有界，再在乘法之前转换到足以容纳其乘积的类型；仅在表达式计算之后强转不能消除溢出。

- 保留原 3 个测试、负 raw、非正 reference/max、raw 大于 max 时钳位的返回语义。
- 24-bit 输入测试只在 `int` 能表达该值时成立；若合同仍支持更窄 int，应条件化该向量并明确宿主覆盖范围，不能用一次 32-bit int host 运行声称所有受支持宽度均实跑。
- 原因链需要真实 native C 的 RED→GREEN，预期由零点、满量程等合同不变量给出，不再复制缩放公式当 oracle。
- UBSan 的支持情况要单独识别；编译器/运行库不支持与产品测试失败应区分。启用了 UBSan 的测试不能靠默认恢复行为打印诊断后仍返回 0 而被误计成功；使用可判定失败的配置并检查退出码/报告。
- 本预审没有执行 ADC，也不将原有 shell 静态检查称为 native C 测试。

无需扩展为整套整数库或跨架构认证。此建议不授权修改外部工具链或真实设备。

## A3：Review 目标的命名必须和实际端点一致

设计已要求单一 diff 端点、已核 baseline 与 overlay，不猜 main、不改 index，符合需求。实施时应明确 working-tree 是哪个差分范围，例如 HEAD→working tree 或 index→working tree；名称、输出 snapshot 和测试断言必须一致，不能取其中一层的 patch 却声称同时覆盖两层。

四种受控 Git 状态应以实际改动标识断言目标 patch 中“应出现/不应出现”的内容，尤其同文件 staged/unstaged 并存和 clean 已提交分支。`git diff --check` 使用同一端点；clean branch 不因为 `git status` 为空就推导没有待审变更。

untracked 文件不属于普通 `git diff` 的 patch。若它们位于声称的完整审查范围，应在 status/coverage 中明确尚未审查或另行读取，不能仅依退出码为 0 声称最新工作树已全量覆盖。这不要求本轮建立全功能 Git 审查工具。

## A4：导出、预算和证据口径继续保持小范围

- 两种 target 的实际导出内容应在没有 ADK 源仓文件的受控目标仓可用；验证默认 handoff 的目标、确认事实、状态/阻塞、权限/scope、raw evidence、下一动作仍在。源仓 schema 的使用需要真正核对 ADK 根和可读文件，不能把目标仓中同名路径误当权威辅助文件。
- `manifests/profile_context_ratchets.json` 仍有 8 个原限额，large-refactor full-source ceiling 为 323328 B；父任务给出的当前余量为 6 B，本预审未重新运行 footprint 测量。最终必须保留原限额，测真实 entry/full-source，而不是靠移动文件到 reference 假装不增加 full-source。
- 只压缩本次已分配路径中的重复说明，保留授权、工具能力、实际执行与证据边界。若需要改其他 Skill 来腾预算，先由 owner 明确写集，不能由实现者越界删减。
- 方法反例、文案静态校验、真实 C/native 工具测试、模型任务试跑与平台发布分别报告。原研究中的 6 项反例检查不能加进 ADK 原回归计数、硬件资格或 agent 成功率。
- 不新增治理层、并行 runtime、外部模型调用或定时任务的范围限制清晰；7 个 Skill 与一个对应示例仍聚焦“已发布指令能正确指导并实际执行”这一问题，未见需要拆成独立产品功能的扩张。

## 后续独立源码审核的入口

实现完成后，由 root 提供最终冻结 diff、候选 HEAD/工作树状态和证据目录。本审核者继续保持只读，逐项检查：

1. 要求 1–7 到真实改动的双向对应，含各个 command/example 的实际执行与反例结果；特别关注 ADC 转换发生位置、CMake 配置/目录/产物绑定和 review overlay。
2. 旧行为保留、真实 skip/不可用项、原预算与完整回归，避免只检查文本关键词或手写替代脚本。
3. 最终 Spec/Quality 双裁决和未验证范围；发布状态按 root 另行提供的真实平台回执核对，不由设计通过推导。

本报告不修改任何实现或计划。可依据本次 design-only pass 启动 T2–T6 已分配实现；最终交付仍须完成 T7/T8 的验证与独立审核。
