# 最终验证与交付边界

## 源码状态

本轮基线 `v11.3.9` / `80f8b2ea2885e3f62dcea455c45a2e8ebf071b2b`；最终待发布源 `v11.3.10` / `d87e21d7750ec4a0042754d045979c137abfc528`，tree `617bdcb20e5fb629c1ddd175e29373b1b86aa0c5`。相对基线 33 个源/测试/合同/审计路径的完整 bytes 和 Git blob 绑定于 `evidence/source-bindings.json`。

完整 canonical patch SHA256：`d82a42ee4620c923ebd4eaecae514f94551a733b4e9627f764a051efab1ab6c4`，528829 bytes。审查者最初短 index 格式的 patch 与该 full-index 版本仅 33 组 index 行表示长度不同；实际两端 blob、路径、hunk 与正文一致。最终审核使用上述 canonical patch，旧格式观察保留。

## 实际验证

| 项目 | 结果 | 原始证据 |
|---|---|---|
| 65 Skills / 153 文件基线复审 | 全覆盖、无重复、422088 bytes 对账相等 | `evidence/portfolio-audit.json` 与三组审计 |
| 外部来源 | 19 个固定仓库 / 6 个官方网页，54 个独立文件或页面；全文 30 / 定向 24 | `evidence/portfolio-audit.json`、`source-review.md` |
| F1/F2 发布命令 | RED 保留；修复后 12 tests、42 次真实调用通过 | `evidence/optional-implementation.json`、`evidence/raw/round3-optional-{red,green}.json` |
| F3 CMake 物理行为 | 4 个修改前后均通过的反例/正常控制，另 14 项已有回归通过 | `evidence/cmake-implementation.json` 与 `cmake-raw/` |
| F3 新消费者 | 实际 B/202、1/1 host CTest 执行通过，24 个旧文件不变 | `evidence/consumer-task.md`、`consumer-response.json`、`consumer-fixture-before.json`、`consumer-materials.json` 及独立消费者复核 |
| F4/F5 新方法测试 | 6 项；真实 validator 5×6 判定、两目标导出的 10 行空表 | `evidence/core-implementation.json` 与 `core-raw/` |
| 最小兼容修复 | 同层 AP marker、原官方文档/意图门禁通过；security 恢复 140 行 | `evidence/core-contract-compatibility-fix.json`、`evidence/optional-line-budget-fix.json` |
| 最终完整回归 | **102/102，exit 0，无超时** | `evidence/full-regression.json`、timing、stdout/stderr |
| 原有 8 个 profile 字节预算 | **8/8 通过，阈值文件逐字节未变** | `evidence/profile-context-checks.json` |

完整回归于北京时间 **2026-11-16 16:14:20–16:19:58** 执行，用时 **338.040357 秒**。前后 HEAD/tree 均为上述最终源且工作树/索引 clean。原始机器回执使用 UTC，stdout SHA256 `0d1bee4e82001511f12291d9c3be0867228a5a396f58b49d3acd176ef3eed61e`；stderr 0 bytes。

首次完整回归实际为 65/102，37 项失败，不能改写为成功。其环境选择错误、两个现有源码门及下游失败分别保留，详见 `negative-results.md`、`evidence/initial-regression.*` 和独立分类报告。第二轮使用已有 Python 3.12.14、继承原 PATH，并显式绑定 `ADK_PYTHON_BIN`；未修改 Python 门禁、测试断言或预算。

## 预算与变动

最终 Skill 资产仍为 153 个文件，合计 **422513 bytes**，相对基线净增 **425 bytes**。改动集中在 5 个 Skills：CMake +555；interface 与 parallel 合计 −425；optional 两项合计 +295。此数据只测仓库 bytes，不构成 Token、运行初始上下文、耗时或成本收益。

`large-refactor` 为 **323321 / 323328 bytes**，余 7 bytes；`embedded-fullstack` 为 **316439 / 316854 bytes**。新增说明继续服从原阈值，不能把现有余量当作可自动放宽的授权。

## 审查与发布状态

独立 reviewer `round3-independent-reviewer` 于北京时间 **2026-11-16 16:23:33** 完成 **Spec PASS / Quality PASS**，0 个未关闭发现。历史 2 major / 1 minor 均为 fixed，绑定上述最终源/tree/canonical patch；报告 SHA256 为 `3f0a5cbea1b7edca923052d313045574410202eb5fd312986dfe596cfb448c56`。实际裁决与 typed digest 映射见本目录 `review-evidence.json` 及 `evidence/independent-source-review.json`，独立原材料映射见 `evidence/independent-retained-files.json`。

证据包装仅追加到已审源码，`evidence/retained-files.json` 映射原执行路径与等字节副本；consumer bundle 对每一项原材料保存内容、编码、大小和摘要。正式 PR、main CI、不可变 Release 三资产实际下载、tag 解析与 Root source-only 接入是后续独立观察，以最终 PR/工作流和发布页面的真实结果为准。本地源码通过与预期发布版本不能预先声明合并或发布成功。

## 明确边界与恢复

- F1 使用合成内容验证，不证明任意敏感文件名自动脱敏。
- F2 仅确认子命令报告的 130/143 或自发信号；父 shell、进程组与真实键盘取消未测。
- CMake 是 Linux x86-64 host-unit；无目标 ABI、板端、RTOS scheduler、HIL 或现场验证。单次新上下文任务不是模型 A/B。
- 未调用外部付费模型或 Codex/Work CLI/Cloud 作业；没有 provider token、费用、稳定胜率或 M5 新资格。
- `~/codex` 不存在；Knowledge Provider 与 Execution Policy 为 unavailable/not-run。沿用用户已授权的 source-only 例外，不写 live 资产、不把不可用标通过。
- 回滚通过既有受保护变更恢复已发布源 pin，并保留本轮失败和审核历史；不删除旧构建证据、不重写已有 promotion 签名材料或历史 M5 记录。
