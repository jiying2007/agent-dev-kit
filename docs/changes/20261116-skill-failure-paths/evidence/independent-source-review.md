# 独立 Spec / Quality 审查：Skills 失败路径优化

**Spec：PASS；Quality：PASS。** 本结论只绑定下面的精确源码。未关闭 blocker / major / minor 均为 0；审查中发现的 2 个 major 和 1 个 minor 已修复，原失败保留。

- 审查者：`round3-independent-reviewer`（`/root/round3_independent_review`），未参与实现或修复。
- 审查开始：2026-11-16T07:55:37Z；最终裁决：2026-11-16T08:23:33.804040+00:00。
- baseline：`80f8b2ea2885e3f62dcea455c45a2e8ebf071b2b`。
- head：`d87e21d7750ec4a0042754d045979c137abfc528`；tree：`617bdcb20e5fb629c1ddd175e29373b1b86aa0c5`。
- 完整源码差异：33 路径；canonical patch：528,829 bytes，SHA256 `d82a42ee4620c923ebd4eaecae514f94551a733b4e9627f764a051efab1ab6c4`。
- 机器可映射报告：`round3-independent-final-review.json`，SHA256 `3f0a5cbea1b7edca923052d313045574410202eb5fd312986dfe596cfb448c56`。完整所审源码身份及真实阅读范围在 `round3-independent-reviewed-source-index.json`；不将自动字节核验描述为全部语义通读。

## 裁决依据

65 个 Skills 的基线人口与三组审计清单相等：34 core、22 embedded、9 optional，共 153 文件、422,088 bytes，零重复/缺漏/额外文件。57 KEEP、5 ENHANCE、3 OBSERVE 的依据已检查。外部来源为 54 个独立快照、55 次观察：19 个固定 commit 仓库的 48 文件和 6 官方页面；原记录声明全文 30、定向 24，摘要与范围一致。来源元数据不能证明人的阅读或完整远端 tree 成员身份，这些边界保留。

| 验收 | 独立判断及实际证据 |
|---|---|
| F1 候选扫描 | 发布的真实 rg 命令验证路径保留、合成内容不回显、1/2 状态分离及覆盖范围。最终句子合并未改变 Commands 至文件尾字节。 |
| F2 中断采样 | 基线复现 130/143 继续采样；修正先保存当轮日志/TSV再原码退出，首轮/后轮、自发信号及普通 0/1/9/124 控制均有实际执行。 |
| F3 构建身份 | 真实 CMake 复现 cache B 但实际 A、clean-first 仍 A；新目录 B 与同 A 增量控制正常。新消费者交付实际 B=202、旧 A=101，原 24 文件完整未变，JUnit 有实际 run。 |
| F4 Schema | 实际提取发布 JSON，真实 validator 执行 5×6 矩阵，保留错误子层封闭、Draft7 忽略关键字控制；同层、现代组合和旧/窄方言分支清楚，未知字段继续拒绝。 |
| F5 空审核模板 | 两个目标实际 export 后沿默认任务包解析引用，5 行空 Evidence 不再预填 pass；使用原 not-run 语义，没有新增门禁。 |

接口三个文件的预算压缩保留版本/能力与 ABI 区分、生命周期矩阵、授权/未知结果对账、反例/原型权限和 not-checked 边界。最后补回的入口 marker 明确带“同层”条件，未恢复无条件组合封闭。CMake 命令块有意保持，因此其证据是方法语义、host 反例/控制和一个新消费者，不能包装为成对模型 A/B。

## 已修复审查发现

| ID | 严重度 | 原始反例 | 最终处理 |
|---|---|---|---|
| R3-REVIEW-01 | minor | 审计正文误写不存在的 adk-worktree-isolation | 仅改为真实 adk-worktree-governance；原审计记录正确。 |
| R3-INTEGRATION-MARKER | major | official_docs / intent_boundary 实际报入口缺 additionalProperties=false | Workflow7 自然声明同层条件，+27B；原 contract/checker 不变，最终两门与 full 通过。 |
| R3-REVIEW-02 | major | security 142 行超过原 140 行 | 只合并两组句子，140 行、−9B；原阈值及 F1 命令/失败语义不变。 |

## 完整回归与预算

首次完整回归仍为失败：`6183982e…`，102 项中 65 pass / 37 fail，exit 1。完整分类记录了 26 段显式 Python guard、4 个在原源码纠正 Python 环境后通过的测试，以及 7 个直接/间接触发上述两个源码门的失败。实际保留的 workflow / integration 报告及 strict JSON 只列这两个已知门；不把全部失败归于环境，也不把 guard 当作没有后继问题的证明。

最终完整回归在准确 `d87e21d7750ec4a0042754d045979c137abfc528` / tree `617bdcb20e5fb629c1ddd175e29373b1b86aa0c5` 上，2026-11-16T08:14:20.475042Z → 08:19:58.536238Z，338.04035697699874 秒，exit 0、无超时。实际注册人口、timing、stdout 的 102 个名称顺序完全相同，102 pass / 0 fail；stderr 0 bytes。receipt 的前后 HEAD/tree/clean 及两个日志的 SHA256 已独立核实，33 个冻结路径在审查时仍逐字节相同。审查者没有重复运行整套 full。

8 个 profile 已用精确归档源码和原生产函数独立重算，与原始 stdout JSON 完全一致；阈值文件与 baseline 字节相同。large-refactor 323,321 / 323,328 bytes，只余 7 bytes。security 140 / 140 行。以上是源码预算，不是 token、运行时上下文或性能收益。

canonical patch 已按主线程的 full-index 参数独立重生并逐字节相等。较早 690599… patch 与 canonical d82a42… 仅 33 个 index 行的 8 位 → 40 位 blob 表示不同，差 2,112 bytes；所有 hunk/路径/正文完全相同，33 组完整 blob 对账通过，旧观察没有改写。

## 必须保留的边界

- 本报告是 source-change 裁决，后续证据包装、受保护合并、fresh-main CI、正式资产与 Root source-only 接入须各自核验。
- 缺宿主 ~/codex 的 native 证据为 unavailable/not-run；没有实际设备、RTOS/HIL、现场、M5、付费模型或 Codex/Work CLI/Cloud 作业验证。
- 102/102 是注册 shell 测试状态，不证明每个嵌套分支或 native/device 路径都运行。F1–F5 的实际方法证据另列，不以关键词或自报 pass 替代。
- 新消费者是单次 host 消费，无独立 transcript 级上下文隔离证明、无成对基线模型运行。前 4 条 bootstrap 没有原始分流 UTC，19 条正式命令的原始分流日志已核；原环境失败保留。
- F1 不自动脱敏文件名或任意真实秘密；F2 不外推到父进程/全进程组取消；F4 不证明所有模型 API 子集；F5 仅对应实际导出的默认包。
- 源审查期间只在 round3-independent-* scratch 下写报告/隔离探针，没有修改仓库、index 或 refs。两次 reviewer harness 错误在原报告中保留并纠正。

## 主要证据

以下每个文件的完整绝对路径、字节数和 SHA256 均在 JSON 的 `evidence_refs`，共有 36 项。

- `round3-independent-stage1-report.md`、`round3-independent-stage1/summary.json`：人口/来源与五个独立基线反例。
- `round3-independent-consumer-review.json`：实际二进制、JUnit、24 文件及原始日志核验。
- `round3-independent-first-regression-classification.json`：完整 37 项失败分类和原始段落。
- `round3-independent-final-regression-verification.json`：最终 full 的身份、原始日志和注册人口。
- `round3-independent-final-profile-recheck.json`：8 个预算重算与原始回执逐项比较。
- `round3-independent-canonical-patch-check.json`：完整 canonical patch 的独立重生/内容对账。
- `round3-independent-reviewed-source-index.json`：所有所审源码/上下文身份、自动核验身份与真实阅读范围。

最终 JSON 为 typed-review 映射提供两个 pass verdict、三个已 resolved 的历史 finding、准确 source/diff、policy/validator 指纹、真实 reviewed_at/evidence_complete_at，以及全部限制。
