# 冻结源码的验证与交付记录

此文件承接 `tasks.md` 在源提交冻结时保留的执行状态；后续仅追加验证、审查与发布凭据，不改写当时的源快照。

## 源码身份

| 对象 | 身份 |
|---|---|
| 基线 | `5f442723e95fa7ca846b7c3ddc9f9995c7a27065` / 11.3.7 |
| 冻结源提交 | `49a20cc96078d6e1206d1d1dcd46761b9dc48d31` / 11.3.8 |
| 源 tree | `df6a691dfcd869ea4fbbfc7674b24538860d9ae4` |
| 变更文件 | 41；远端 tree 与本地 staged tree 相同后 fetch 核验，再对该 canonical SHA 执行回归 |
| 原始完整 patch | `evidence/original.patch`，485,382 B，SHA256 `7e2b67d92cfe9f1a2b175710e2a526a306b06ec5282bc69cdafcd01494423175` |

Patch 禁用 external diff/textconv/FSMonitor，固定完整路径、颜色和子模块差异语义，包含 binary/full-index。共有 41 个行首 diff header；归档的原观察本身也含有 diff 文本，不能用全文子串计数代替文件数。

## 实际验证

| 验证 | 观察结果 | 原始凭据 |
|---|---|---|
| 全量回归 | 102/102 组通过，0 失败；外层 309.528 秒；exit 0 | `evidence/full-regression.json`、`full-regression-timing.json` 与两份完整 stdout/stderr 日志 |
| Skill 内容组 | 140 个 unittest 通过，含本轮 11 个新增真实执行测试 | `evidence/full-regression.stderr.log` |
| 源码冻结 | 回归开始/结束的 41 个文件 SHA256 完全相同；回归完成时工作树 clean | `evidence/full-regression.json` |
| Profile 体积 | 8/8 原有 ratchet 通过；large-refactor 323,288 / 323,328 B；阈值未改 | `evidence/profile-final.json` |
| 全量审计 | 65 个入口、53 个参考，覆盖全部 152 个基线 Skill 文件；8 增强、57 保留；净减 92 B | `evidence/portfolio-audit.json` |
| 中间失败与反例 | Git helper/配置反例、C 优先级错误、无效夹具、初次容量超限和版本同步失败均留存 | `negative-results.md` 与 `evidence/raw-observations.json` |
| 方法消费 | 同一新消费者会话处理 3 个工程案例，最终输入哈希和修正后重读历史均保留 | `evidence/consumer-task.md` 与 `consumer-response.json` |

本地全量回归于 `2026-11-16T04:07:02.454699Z` 开始，`2026-11-16T04:12:12.007854Z` 完成。工具为 Python 3.12.14、Git 2.52.0、CMake 3.31.6、Ninja `1.11.1.git.kitware.jobserver-1`；原测试超时预算未变。工具存在后的 CMake/Ninja 用例为实际执行，未以缺工具跳过替代通过。

## 独立审查

审查者没有参与实现。其初审发现两个问题：6 个变更 Skill 沿用旧版本、protocol 压缩丢失各层独立状态机的明确约束；这两项在冻结前修正。`evidence/independent-source-review.json` 于 `2026-11-16T04:14:45Z` 给出 Spec/Quality 双通过、0 未关闭发现，保留 12 条结论边界。审查者还实际构建了含 47 个 Skill 的临时 bundle，核实 8 个新版本路径和新增 transport reference 随包交付；没有运行外部 importer。

`review-evidence.json` 机械映射独立报告的结论与已关闭发现，绑定上述源提交、完整原始 patch、41 个实际输入摘要和回归凭据。现有 typed validator 实际通过，结果在 `evidence/review-validation.json`；摘要校验不代替独立语义审查或平台交付观察。

回归完成后追加的证据文件使工作树进入证据打包阶段；不能将“回归完成时 clean”误写为“此后整个工作树始终 clean”。这些追加文件不改变冻结源提交的 41 个文件。

## 交付与结论边界

- T1–T5 已完成：全量审计、方法实施、完整回归、源码冻结及独立 Spec/Quality 审查均有实际凭据。
- T6 经普通 PR、精确 head 的保护检查、正常 squash merge、fresh-main CI 和既有 immutable release 流程完成；平台结果在 PR 中按实际观察补记，未在本文件预填成功。
- v11.3.7 的历史 CTest 超时原因仍未知，本次本地绿色不构成根因修复。
- 源码字节变化不代表真实 Token、费用或原生上下文节省。三案例是新会话消费观察，不是盲测、重复 A/B 或模型效果资格。
- 真实模型、板端/HIL、用户宿主安装和当前源码的现场资格均未执行或未测；组件发布与源码消费升级不替代这些证据。
