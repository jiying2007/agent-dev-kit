# 验证与发布边界

运行源码冻结：`9a918fa33e02313681649a52713d04750ef0bf0b`；基线：`008c789312ed374f38d6d71a113f8fc91f89e63c`；版本：**11.3.6**。完整 patch SHA-256：`f25ae36bf5504c3a5127f07fdd6a3c54a032a6fb48beeb7d20ab0f74ebde4f57`。冻结 30 个变化源码及合同路径；后续封装只增加本轮审查/验证材料。

## 完整入口与实际边界

执行 `bash tests/run_all.sh --fail-fast --timing-json <本 change>/evidence/full-timing.json`。

- 开始：2026-11-16T01:04:19.453333Z。
- 结束：2026-11-16T01:09:15.949071Z。
- **102 个测试组通过，0 组失败，exit 0；296.495747 秒。** 这是组数，不是单个断言数。
- 30 个冻结路径执行前后摘要一致；compact log、timing、source freeze 和真实回执一并保留。紧凑成功日志不会输出每个成功子测试，也不以日志文本相同表示运行相同。
- 当前 command-example 模块 26 项中，**21 PASS、5 个真实 CMake case 本地明确 SKIP**。GitHub Actions 环境缺必需工具会 FAIL；最终合并前必须确认该平台实际执行成功，不能把本地组 PASS 当 CMake 实跑。

首次冻结 `e0c3b97…` 的完整入口只执行 6 组（5 PASS、1 FAIL），因 review 入口缺原 SOP 字段失败；27.405 秒、exit 1。原 source/patch/log/timing/receipt 完整保存在 `evidence/attempt1`。恢复实际字段后使用新冻结重跑，没有修改测试或门禁。

## 定向与独立证据

| 范围 | 实际结果 |
|---|---|
| 审查 patch 范围 | 实际导出到两个目标，覆盖四种 Git 状态；核 untracked、whole-branch overlay、无效基线以及 index/源码不变 |
| Git stat-only 反例 | 默认 diff 会刷新 index；只加 optional-lock 参数的中间方案仍失败；命令局部 `diff.autoRefreshIndex=false` 通过原反例 |
| Context 导出 | 两个 target 的真实 core 包不含源仓辅助 schema/template，正文仍有目标、事实、状态、scope/permission、证据与下一步 |
| ADC host | 原三个用例保留；native 与受支持 UBSan 先真实失败、修复后通过；本机实际 14 个 C 向量 |
| ADC 独立编译 | 审查者将实现按 C11、消费者按 strict C90 分别编译再链接执行，14 个向量通过；验证 PRIVATE 语言边界 |
| CMake 五场景 | 非默认 preset 名称/目录/Release、manual RelWithDebInfo、空测试、compile-only、真实 ADC 工程 C11 接线；本机缺工具，实际构建留给 PR CI |
| 方法反例 | 堆活跃 payload、共享进程顺序、整数时钟与嵌套尝试的六个检查通过；是受控方法模型，不是 agent A/B 或设备测量 |
| 最后 SOP 修复 | 完整 SOP 脚本通过，三个 T2 定向方法通过；独立审查者再次在最新冻结复跑两个核心方法，2/2、0 skip |

## 预算与门禁

最新冻结上的 strict、内容预算、module-size、release source check 全部通过。原 `manifests/profile_context_ratchets.json` 与基线逐字相同；八个 Profile 均在原上限内。

| Profile | 入口源码 B | 含按需资源 B | 原总上限 B |
|---|---:|---:|---:|
| core | 98,496 | 173,552 | 184,133 |
| release-hardening | 83,145 | 157,226 | 159,576 |
| personal-core | 113,428 | 192,221 | 204,293 |
| embedded-fullstack | 211,227 | 316,321 | 316,854 |
| team-core | 123,962 | 211,387 | 223,333 |
| large-refactor | 214,252 | 323,203 | 323,328 |
| incident-response | 30,800 | 46,556 | 46,612 |
| research-intake | 65,806 | 118,021 | 124,543 |

SOP 字段恢复使 review 入口增加 346 B；不宣称每个 Skill 或每个总源码表面都变小。这里测的是源文件字节，不是宿主实际加载量、provider Token 或任务质量。原 65 个注册身份、权限、安装边界与发布门禁保持。

## 独立审核与平台资格

独立审核由未编辑实现的 `ai/root/external_skill_scan_v2` 承担；正式 Spec/Quality 裁决见 `evidence/independent-final-source.json`、`evidence/independent-final-review.md` 与 `review-evidence.json`。本页先记录已发生的运行结果，不能替代该审核。

源码通过只允许按既有流程提交候选并取得平台证据。合并仍要求最终 PR HEAD 的必需检查成功、五个 CMake case 在 GitHub Actions 实际运行，再核 main CI、自动 tag 和正式 Release。本地尚未执行 ruff/mypy、CMake/CTest/Ninja、Valgrind、ARM 交叉编译或板端验证；平台结果不能倒写为本地结果。

上一轮 **11.3.5 已闭环**：PR #270 正常 squash 到 `008c789…`；main CI `43782374659` 成功；自动发布流程 `43782987159` 成功；annotated tag `v11.3.5` 指向同一 main，正式 Release 为 immutable，含 tar.gz、SHA256 和 release-contract 三个标准资产。实际回执为 `evidence/prior-publication.json`；未修改上一轮历史 blocked 记录。

无外部模型/API、Codex/ChatGPT Work Cloud/CLI 额度调用、计划任务、生产部署或设备写入。模型成功率、Token、费用和设备性能仍未测量。
