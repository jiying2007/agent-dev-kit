# 11.3.6 最终独立源码审查

## 裁决与适用范围

**Spec：PASS（源码提交范围）；Quality：PASS；开放 source blocker = 0、major = 0。** 当前源码可提交既有 PR CI。**merge readiness 与 release readiness 仍为 false**：需求 7 的五个真实 CMake/CTest 场景尚未在本机执行，必须在最终 PR HEAD 的 CI 中实际通过，之后继续履行既有合并与发布检查。

这不是要求新增审批。它区分“源码已经可送检”和“所需平台执行证据已经取得”。本机整套入口通过不能替代缺工具而跳过的五个 CMake 场景。

- Reviewer：`/root/external_skill_scan_v2`，受 `/root` 委派；未编辑实现。
- 正式审查时间：**2026-11-16T01:12:41.916238Z**，晚于证据输入封装完成时间 **2026-11-16T01:11:27.082036Z**，也晚于完整回归完成时间。
- 工作树：`/workspace/scratch/2d6ca6dc3d38/adk-practical`。
- 方法：完整冻结 diff、相关上下文与合同、证据包装核对、有限独立执行。属于实现后独立审查；不是 blind model A/B。阅读了源码和测试断言，没有据预期答案修改 Skill。
- 范围：30 个冻结源码/合同路径，涉及 7 个已有 Skill、已有 ADC 示例及对应测试/版本文档。未声称本轮重新执行了全部 65 个 Skill 的模型任务。

## 精确对象与证据身份

| 对象 | 核验值 |
|---|---|
| Base | `008c789312ed374f38d6d71a113f8fc91f89e63c` |
| Final head | `9a918fa33e02313681649a52713d04750ef0bf0b` |
| Tree | `bef1da3b91570b849d5e7373b9ab545e09b823aa` |
| 完整 source patch SHA-256 | `f25ae36bf5504c3a5127f07fdd6a3c54a032a6fb48beeb7d20ab0f74ebde4f57` |
| 冻结路径数 | 30 |
| 交付输入数 | 72 |
| 输入索引 SHA-256 | `cac7b9a72611378daa1fa67767731cccea844c024cf2627d22c080f0bb9c9021` |

30 个工作文件均与指定 commit blob、source-freeze 的 SHA-256 一致；实际 base→head 的完整 diff 与归档 original.patch 摘要一致。完整 patch 的 `diff --check` 退出 0。原 profile ratchet、GitHub workflow 与 SOP gate 相对基线没有变化。

72 个封装输入逐项核对 SHA-256 和字节数通过。这里的 72 是输入完整性条目数，不是运行测试数。交付说明两处历史回执引用已修正并纳入这份索引；后续拷贝本报告或生成 typed 封装记录不应倒填已审输入。机器可读报告列出全部 30 个源码摘要和独立原始回执身份。

## Spec 审核

| 需求 | 判断 | 依据与边界 |
|---|---|---|
| 1. Review diff 对象 | PASS | staged=HEAD→index；working-tree=HEAD→已跟踪净工作树；whole-branch=已核基线的 merge-base→HEAD。保留 dirty/untracked overlay、缺基线失败与 index 不变。实际导出到两 target 的受控 Git 场景通过。 |
| 2. Context/handoff 默认自足 | PASS | 实际 core 导出不含 ADK 源码辅助 schema/template；默认正文仍保留目标、事实、状态/阻塞、scope/permission、证据与下一动作。仅在核实源码根和可读性后选用辅助文件。 |
| 3. ADC 整数边界 | PASS | 运算前拓宽、声明整数宽度约束，保留错误返回、钳位和整数截断。native、受支持 UBSan、独立分开语言编译/链接和 14 个端点向量通过。CMake 接线的实际执行归入需求 7 待 CI 项。 |
| 4. 性能测量方法 | PASS | 堆峰值/时间线用 Massif，错误/泄漏用 Memcheck，RSS 另列；工具可用性、采样口径与插桩扰动明确。未把逻辑堆模型当 Massif 或 RSS 实测。 |
| 5. flaky 同进程污染 | PASS | 仅有 suite/独跑差异或共享状态线索时展开矩阵；保持顺序、seed、worker、进程边界，比较前序→victim 与反序并缩小前序集合。承认多个污染者可能有非单调交互。 |
| 6. 协议总预算与重试责任 | PASS | 阶段、尝试、退避计入整体剩余时限；嵌套重试核总量。保留协议必要重传、错误语义、非幂等 UNKNOWN 对账、跨主机时钟与长连接寿命边界。 |
| 7. CMake 目录/configuration | 源码 PASS；实跑待 CI | preset/manual 互斥并绑定实际 binaryDir/configuration/test backend/ELF。五个真实 fixture 与缺工具 CI 失败条件已审；本机缺 cmake、ctest、ninja，不能宣布 runtime 验收完成。 |
| 8. 原门禁、版本、证据层次 | PASS | 11.3.6 版本一致；8 个原 ratchet 未提升；最新完整回归 102/102。方法反例、作者历史、独立审查、源码回归与平台发布分别记录。 |

### Review 与随包交接

发布模板使用与所选 patch 相同的参数执行 `diff --check`，whole-branch 明确记录 base/merge-base/head。working-tree 不把被覆盖的 staged 中间态冒充最终净工作树；untracked 路径由 status 呈现，正文是否单独读取须有 scope 决定。命令局部 `diff.autoRefreshIndex=false` 处理了真实 stat-only 自动刷新反例，不只依赖 optional-lock 开关。

独立最终复跑使用实际 `render_asset` / `export_assets`，涵盖 claude-code/opencode、四种主要 Git 状态、overlay、无效基线、stat-only 以及源文件/index 不变。context 检查实际消费包缺少源码辅助文件时仍可依默认字段交接。两个 test method 包含多场景，不夸计为独立模型任务。

恢复后的入口有真实紧凑 Evidence Template：`Snapshot ID:`、`Working Tree Overlay:`、`Reviewer Independence:`、`Review Round / Mode:`、`New Finding Class Count:`、`Mechanical Gate:`、`Contract Change Decision:`。这是实际填写字段，不是为门禁加入的注释；既有独立性、scope、最终 whole-diff 与 readiness 分离仍在正文/随包 reference 中。

### ADC 数学与语言边界

验证和钳位后，`0 <= raw <= max_count <= INT_MAX <= INT32_MAX`，且 `0 < reference_mv <= INT_MAX`。最坏乘积为：

`(2^31 - 1)^2 = 4611686014132420609 < INT64_MAX`。

转换在乘法之前发生，除数严格为正，商落在 `[0, reference_mv]`，所以中间量和返回到 int 的转换均可表示。端点期望来自零点、满量程、钳位、无效输入不变量；没有复写实现公式生成答案。

`_Static_assert` 在实现中；既有 CMake target 的 `PRIVATE c_std_11` 与实际需要一致，cross smoke 显式 `-std=c11`。独立把实现按 C11、调用测试按 strict C90 分别编译，再链接执行，14 个向量均通过。这能证明当前消费者不需要传播 C11 语法要求，不能冒充真实 CMake 或 ARM cross 构建。PRIVATE 作用范围和 C11 feature 支持分别对照了 [CMake 3.16 target_compile_features](https://cmake.org/cmake/help/v3.16/command/target_compile_features.html) 与 [C language features](https://cmake.org/cmake/help/v3.16/prop_gbl/CMAKE_C_KNOWN_FEATURES.html)。

### CMake 方法与五个真实 fixture

源码审核确认 preset 从 source cwd 运行，build/test preset 关联已核 configure preset，其 binaryDir 与 configuration 一致；名称不必相同。manual 使用明确 source/binary/toolchain/generator/config，CTest 使用同一配置，artifact 只消费成功构建的实际 ELF。host-unit/emulator/board-runner 与 compile-only 分开；后者输出 not-run，不伪造测试通过。

五个 fixture 检查不同 preset 名称及目录的 Release、manual RelWithDebInfo、空测试失败、compile-only 不执行 CTest、真实 ADC 项目在 strict C90 默认下的 PRIVATE C11 接线。测试在有工具时真实创建 CMake 工程、构建、执行 CTest、核配置身份/ELF 和产物命令，避免只检查 shell exit 0；旧目录哨兵用于检验错误目录未被消费。API 语义核对了 [CMake Presets](https://cmake.org/cmake/help/v3.27/manual/cmake-presets.7.html) 与 [CTest](https://cmake.org/cmake/help/v3.20/manual/ctest.1.html)。

**这些是对可执行 fixture 的源码审查，不是本地已执行声明。** 本机五例明确 skip；独立设置 `GITHUB_ACTIONS=true` 后五例都因缺工具 fail、进程 exit 1，符合预期拒绝行为。该负例只证明 CI 缺工具不能跳过变绿，实际 CI 仍必须跑成功。

### 方法删简与边界保持

性能正文继续保留工作负载有效性、环境/源码身份、ABAB、KPI、invalid/inconclusive/no-gain 和原始证据；此次纠正工具目的，不以 Valgrind 插桩耗时推断原生性能。工具定位对照 [Massif](https://valgrind.org/docs/manual/ms-manual.html) 和 [Memcheck](https://valgrind.org/docs/manual/mc-manual.html)。

协议保留执行目标、主动采集/注入的授权、新 PCAP 与零样本失败、measured/inferred/unknown 区分。flaky 保留准确测试分母、精确退出码、样本不足、超时/取消、环境值保密、quarantine 不计 PASS。早审的“Retry-After 延后”与“无条件隔离”建议都已落实，不存在因压缩而扩大权限或虚增执行证据的发现。

## Quality 发现与闭合

| ID | 状态 | 实际发现与闭合 |
|---|---|---|
| F1 | 已闭合 | 首次全入口在 e0c3b97 上因 review 入口缺 SOP 标识失败：6 组总计、5 PASS、1 FAIL。恢复七个实际字段；不改 gate/test；新冻结完整 102/102 与独立最终两方法通过。旧 source/patch/log/timing/receipt 保留。 |
| F2 | 已采纳 | 协议旧“延后”可能被误解为复活已过期预算。最终明确先结束本轮，业务延期另按语义处理。 |
| F3 | 已采纳 | flaky 旧步骤无条件隔离。最终改为按需，验证边界并保留原失败状态。 |
| F4 | 已闭合 | T2 task 对旧 green-index-refresh 的最终性表述改为历史阶段，并指明后续 SOP 和最新完整回执。 |
| F5 | 已闭合 | 包装中的 general/red.json 更正为实际 general/results.json。 |

当前未发现开放 blocker/major/minor。F1 由整合者完整回归揭示，本审核者核实修复与新回执；没有把早期两方法通过描述为早期整套 SOP 已通过。早期报告、包含 green 字样的失败文件、不同 source SHA 的历史回执均保持各自身份。

## 实际验证与归属

| 验证 | 结果 | 执行者/证据界限 |
|---|---|---|
| 完整入口 | 102 组 PASS、0 FAIL、exit 0；296.495747 秒 | /root 执行；本审查独立核源码身份、30 路径不变、receipt/log/timing SHA 和 102 条状态。未另跑全套。 |
| 最新导出 Review/context | 2/2 PASS、0 skip，约 0.569 秒 | 本审核者于 2026-11-16T01:09:53.102658+00:00 完成，直接在 9a918fa 上执行。 |
| native ADC 两方法 | 2/2 PASS、0 skip，受支持 signed-overflow sanitizer 实跑 | 本审核者在 e0 快照执行；七个相关源/测试路径与最终冻结逐字一致。 |
| C11/C90 分开编译、链接、运行 | 四命令 exit 0，14 C 向量 PASS | 本审核者实际执行。 |
| CMake 缺工具 CI 拒绝 | 预期 exit 1，实际 exit 1，五例因缺工具 fail | 本地模拟 CI 环境标识；不是平台 CI 或 CMake 构建。 |
| 原 profile ratchet | 8/8 PASS | 本审核者用仓库真实 enforcement 函数独立重算；policy 与 base 相同。 |
| strict/content/module-size/release source check | 全部 PASS | /root 最新 final-gates 回执绑定 9a918fa，本审核者核读；不是正式发布成功。 |

完整运行开始于 **2026-11-16T01:04:19.453333Z**，结束于 **2026-11-16T01:09:15.949071Z**。最终回执 SHA 为 `11ff5e4bf00dbfa5b9fc3f17c3bcb8b6d397c207ab247b5e63f47cdb8055ac30`，full.log SHA 为 `0d1bee4e82001511f12291d9c3be0867228a5a396f58b49d3acd176ef3eed61e`，timing SHA 为 `12c9c41389943439df3b447ecd7f99e3d0d1d08ccc36d9e8c4bb8971319f8593`。紧凑日志不会输出所有通过子测试；102 计顶层入口，不含有意跳过 CMake 的“真实成功”推断。

原预算独立结果：

| Profile | 入口源码 B | 含资源总源码 B | 原总上限 B | 状态 |
|---|---:|---:|---:|---|
| core | 98,496 | 173,552 | 184,133 | PASS |
| release-hardening | 83,145 | 157,226 | 159,576 | PASS |
| personal-core | 113,428 | 192,221 | 204,293 | PASS |
| embedded-fullstack | 211,227 | 316,321 | 316,854 | PASS |
| team-core | 123,962 | 211,387 | 223,333 | PASS |
| large-refactor | 214,252 | 323,203 | 323,328 | PASS |
| incident-response | 30,800 | 46,556 | 46,612 | PASS |
| research-intake | 65,806 | 118,021 | 124,543 | PASS |

large-refactor 余量为 **125 B**。这是源文件字节的增长约束，不是宿主实际上下文、provider Token 或费用测量。不要据此声称每个 Skill 都缩小或任务质量量化提升。

## 后续必须取得的证据与限制

最终 PR HEAD 必须实际执行上述五个 CMake case，并满足现有必需检查后方可合并；之后仍需 main CI、正常 tag/Release 核验。若平台工具缺失或某个 fixture 失败，应处理实际失败而不是放宽门禁。这里只判定源码可送检，没有给 merge/release readiness。

本轮没有执行 ARM cross smoke、板端/真实设备、Valgrind profiler、原生 Agent host 模型任务或外部模型 API；没有模型成功率、Token/费用、硬件性能改善数据。受控时钟/重试/堆活跃量/共享状态反例说明方法维度，不能累计为 agent A/B 或现场测量。上一轮 11.3.5 的远端发布资料由整合者提供，本审核者未独立访问远端平台对象。

## 本报告原始证据

- `source-review.json`：正式裁决、30 个 source SHA、72 输入边界、分开 Spec/Quality、已闭合发现、真实运行归属与 readiness。
- `final-verification.json`、`final-two-methods.log`、`verify-final.py`：最新源码两方法执行与整套回执完整性核对。
- `targeted-verification.json`、`run-targeted.py`：ADC/native 语言边界与缺工具 CI 拒绝原始执行。
- `snapshot-check.json`、`independent-profile-budgets.json`：最终 source/tree/patch 对照和原预算独立计算。
- 同轮早审与研究保存在 `research-v2/general-review`、`root-method-review.md`、`design-review.md` 和 `external-skill-findings.md`，各自的早期来源身份保留，不覆盖最终绑定。
