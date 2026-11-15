# 外部方法优化的验证结果

## 冻结源码与完整回归

基线是已发布 `v11.3.3` 的 `5e0e83bcc127665de9a352e9eacfe9b092106cb2`。本轮最终源码为 `cd1d9b316facff73bcec0ed39d3a942a959292e4`，tree `9020ba384be332dbd95575044da6b84313706c64`，在 `2026-11-15T14:48:40.189890Z` 冻结。48 个变更文件的 SHA256、Git blob、模式与大小见 [源码绑定](evidence/source-bindings.json)，完整原始补丁见 [original.patch](evidence/original.patch)。原补丁 SHA256 为 `6ef7ac27cc4c6bdde40dacf230731f4a320035f43c9531c8ca568f70ed148383`。

完整回归实际在本地检出上述已推送提交运行，从 `2026-11-15T14:48:40.321722Z` 至 `2026-11-15T14:57:33.375706Z`，Python 3.12.14，**102/102 组通过、0 失败、exit 0**。入口为 `bash tests/run_all.sh --fail-fast --timing-json ...`；本次没有提前退出，实际完成全部注册组。入口计时为 532510 ms，外层包含启动及落盘为 533053 ms。

回归前后 48 个文件摘要完全一致，HEAD 未移动，工作区恢复干净。[原完成回执](evidence/full-receipt.json)、[逐组计时](evidence/full-timing.json) 与 [完整原日志](evidence/full-log.json) 保留实际结果。随后提交只新增验证与审查材料；最终 PR HEAD 的受保护 CI 将覆盖包含这些材料的完整树，不能把此前本地结果冒充后续 CI。

## 方法与实际观察

| 范围 | 结果与适用范围 |
|---|---|
| 全部 Skill 审查 | 两组共 56 core + 9 optional，65 个唯一身份、143 个实际读取路径；独立复核全部路径 SHA256/Git blob 对齐基线。6 项直接方法增强、1 项条件性交接增强、58 项保留及其具体理由见 [逐项审查](audit.md)。覆盖清单不代表所有 Skill 的真实模型使用效果已测量。 |
| 外部来源 | 实际读取 17 个原始仓库的具体 Skill、reference、脚本或规范材料，并以 10 项工具官方文档/代码交叉核查。全文与选读范围、固定版本、许可限制、拒绝做法及过期路径见 [来源审查](source-review.md)。目录发现和搜索片段没有计作原文精读。 |
| 兼容迁移 | 直接执行最终公开参考中的 Python 包与两个真实消费者：提前删除旧接口失败；expand、消费者逐批迁移、最终 contract 保持预期输出。普通纵向切片仍为默认，真实数据迁移/删除/发布权限未扩大。 |
| 独立期望值 | 实际错误变体能骗过共享被测 helper 生成的 expected；契约派生期望值拒绝错误变体，正确实现和合法边界通过。不是全仓 mutation 评测。 |
| 检查器校准 | 执行公开 scanner/checker 命令；干净及阈值内报告通过，违规、执行错误、未知级别、缺字段、空/未完成/非 JSON 报告拒绝。进程成功、报告完整性、严重度阈值分别判读。只在新建、修改或可疑 checker 时启用。 |
| 性质与状态序列 | 最终标准库 host 示例枚举 121 个序列、426 步，独立队列模型发现 `[1, 0, 2, 0]` 反例；这是给定有限操作字母表中的最短反例。干扰序列之后重放一致；修复实现全部通过。`python3 -I` 保证不会因环境优化关闭 assert。没有运行 Hypothesis/libFuzzer 或板端任务。 |
| Sanitizer | 实际 GCC 14.2.0 / x86_64 signed overflow：默认 recover 报警且 exit 0，关闭 recover 报警且 exit 1，修复后 exit 0 且无诊断。前两者是工具成功报告程序缺陷，被测程序未通过验证。其他编译器、ASan/TSan、目标 runtime 未运行。 |
| 栈资源 | 实际 GCC `-fstack-usage` 公开程序得到 leaf 288 B static、caller 432 B static、dynamic_frame 48 B dynamic，同一构建运行含 4096 B VLA 的路径。数值仅属于本次 host 构建；max(frame) 或 dynamic 行固定数值不能直接作为任务栈上界。dynamic,bounded、IRQ/RTOS port、实际 high-water 和板端峰值未执行。 |
| 新增与既有测试 | 新增 8 个 core + 4 个 domain 测试进入既有 Skill 内容组；作者完整内容检查为 94/94，独立执行新增模块为 12/12、0 skip。完整 102 组回归再次执行现有内容与触发检查，不增加组数、不放宽原断言。 |
| 发现与权限 | 已修复裸名词造成的概念解释/非嵌入式误路由。领域 6 正例、8 反例通过单 Skill 与全目录生产 Matcher；独立另测 5 组新增词与原 non-trigger 组合，共 10 个 CLI 调用均拒绝，auto 为 abstain/deny。生产 Matcher 与原权限契约未改。 |
| 导出可达性 | core 三类方法测试直接消费真实导出；domain 测试读取公开源代码 fence。独立先对 7 项 Skill × Claude Code/OpenCode 做 14 次 `render_asset`，10 个自身参考路径在两目标上的 20 条携带检查通过。completion 正文恢复后，独立又对这 1 项 Skill 的两个目标执行渲染：constraints 被剥离，11 字段、模板路径、条件与 owner/效果/rollback 仍留在正文，自身 reference 字节一致。其余未变文件按原摘要复用，旧记录不重写为新执行。上述均为确定性导出结果，未冒称原生宿主实际加载。 |

原作者执行与失败记录见 `evidence/core-diagnostics.json`、`evidence/core-budget-followup.json`、`evidence/domain-diagnostics.json`。独立执行原件、前后摘要和实际命令见 [独立执行归档](evidence/independent-observations.json)。所有数量按各自分母陈述，不能相加为模型任务或设备任务数量。

## 易用性和源码体积

7 项修改入口的 UTF-8 源码合计从 **32,227 B 降至 24,488 B**，减少 **7,739 B（约 24.0%）**。新增必要参考后，本轮 Skill 文件净增 **701 B**。重复散文被精简，协议/数据/安全/发布的专项适用条件、回退/环境信息及 CLI/noninteractive 场景保留；普通任务不会无条件加载六类新方法。正文恢复后重新核算全部数值，没有沿用前一冻结的更小入口数字。

| Profile | 入口字节：11.3.3 → 11.3.4 | 全部潜在源码字节：11.3.3 → 11.3.4 | 原上限 | 结果 |
|---|---:|---:|---:|---|
| core | 106,348 → 101,097 | 175,439 → 173,849 | 184,133 | pass |
| release-hardening | 93,379 → 85,640 | 156,716 → 157,417 | 159,576 | pass |
| personal-core | 121,119 → 115,868 | 193,947 → 192,357 | 204,293 | pass |
| embedded-fullstack | 221,389 → 213,650 | 315,739 → 316,440 | 316,854 | pass |
| team-core | 131,661 → 126,410 | 213,121 → 211,531 | 223,333 | pass |
| large-refactor | 224,414 → 216,675 | 322,621 → 323,322 | 323,328 | pass |
| incident-response | 35,247 → 30,804 | 46,565 → 46,560 | 46,612 | pass |
| research-intake | 70,981 → 68,094 | 119,738 → 118,124 | 124,543 | pass |

基线等价 tree 与原预检保存在 [集成预检](evidence/integration-preflight.json)，上表当前值来自 [正文修复回执](evidence/completion-contract-fix.json) 中的最终 8-profile 原件；最终冻结全量也通过原有 profile/context 组。8 个原阈值未提高。表中的“原上限”为全部潜在源码上限，入口另有原阈值并通过。字节、静态 token 估算和运行期实际 Token 不可互换；未测模型延迟、费用或任务成功率。

## 真实失败与修复

第一次冻结 `58f25a4e23d17e2e128cedbf791f3ea76d3653e5` 的全量入口实际 exit 1，在 `test_catalog` 处 fail-fast，只有 **2 pass / 1 fail**。五项描述改进未同步生成目录是根因；修复使用既有生成入口更新目录，没有改测试或生成器。原失败完整回执保留在 [目录失败归档](evidence/catalog-drift-failure.json)，后续成功没有覆盖首次结果。

第二次冻结 `5f42c1b096b702fbcfb4debb57115b21bc872f06` 的目录组通过，随后在第 99 组 `test_capability_uplift` fail-fast，实际 **98 pass / 1 fail、exit 1**。去重时把 Codify 字段移至 reference，遗漏了原消费者要求的主正文可见性；`delivery_goal` 是第一个报错项。原完整日志、计时和独立失败复核保存在 [完成字段失败归档](evidence/completion-contract-failure.json)。

修复重新核对四个原 checker，将全部 11 个 Codify 字段和权威模板路径移回既有 goal-final/适用晋级分支；checkpoint 保持 deferred，reference 删除重复字段列表并指向同 Skill 正文，owner/效果/回退条件及可执行示例未改。两文件净增 15 B；原 capability 检查实际红→绿、94 项内容与 8 原预算通过。最后三组补充预检在未冻结工作区执行，单列其范围；最终完整第三次运行才是本报告的 102/102 依据。没有修改原测试、四个 checker 或预算阈值。

此前定向描述契约失败、独立预审 M1 误路由、精简时专项完成条件的修复和中间 profile 超额均保留在 [负结果](negative-results.md)。历史报告保持原时间/原摘要，最终源码与报告适用性由后续绑定和独立复核说明；不能倒填历史 PASS。

## 独立审核与交付边界

独立 reviewer 只读，正式 Spec / Quality 与发现处置见 [审查原文](review-findings.md)、[独立绑定](evidence/independent-review-binding.json) 和 [机器校验记录](review-evidence.json)。声明 AI 身份不等同已认证人类身份或 GitHub approval；摘要校验本身不产生语义裁决。

公开归档采用 UTF-8 文本无损包装，字节数与 SHA256 对应真实原件；本轮没有通过编码隐藏匹配值或放宽安全扫描。原有 format 的脚本可执行位警告仍保留。环境没有 rtk，使用实际 Bash/Python 原入口；没有安装或伪造包装器。

本轮未执行付费模型调用、真实模型 A/B、独立最终 holdout、原生宿主使用认证、板端/HIL/真实内核/实时采集、真实邮箱或用户电脑操作。确定性测试、host 反例及来源吸收证明其明确范围，不能转写为上述未运行结果。

此文记录的是本地冻结验证与待受保护交付状态。最终 PR HEAD、8 项必要检查、正常 squash、main CI、annotated tag 和 canonical release 的完成，以随后真实 GitHub 事件为准；源码审查或本地通过不能替代它们。
