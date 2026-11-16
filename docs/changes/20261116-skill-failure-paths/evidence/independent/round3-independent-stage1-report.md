# Round 3 独立审查：阶段一证据核验

Reviewer：`/root/round3_independent_review`（AI，只读；未参与本轮实现）。

## 结论范围

阶段一未发现阻塞审计清单或五项缺陷立项的实质问题。基线人口、每个文件身份、处理决定、外部快照身份及阅读范围声明之间一致；五项原始失败均在独立隔离目录中重现。

这不是对当前实现补丁的 Spec/Quality 最终批准。当前源码尚未按父线程提供的 frozen commit/tree 审查；修复后完整回归、预算、消费者回执及发布/Root 接入均不由本报告认定通过。

## 时间与源码身份

- 审查启动时钟：2026-11-16 07:55:37 UTC。
- 独立探针实际运行：2026-11-16T07:58:17.585315+00:00 至 2026-11-16T07:58:20.250886+00:00。
- 基线 commit：`80f8b2ea2885e3f62dcea455c45a2e8ebf071b2b`（v11.3.9）。
- 基线 tree：`ada1992f60ad6980bf8e1474db8a2a1b247c5c28`。
- 精确基线导出来自 `git archive` 的隔离副本，未从正在变化的实现工作区导入 exporter。
- 全部 shell 经指定 `verification-tools/rtk`；原始读取用 bypass/Python。没有仓库、index、refs、外部服务或设备写入。

## 人口与来源核验

直接对 Git baseline tree 计算 65 个 Skills、153 个文件、422,088 bytes。core 为 34 / 93 / 231,726；embedded 为 22 / 45 / 123,379；optional 为 9 / 15 / 66,983。三组路径无重复、遗漏或额外项；逐文件 blob、SHA256、字节数、行数与各报告及整合清单一致。

65 项决定恰好覆盖全部 Skill：57 KEEP、5 ENHANCE、3 OBSERVE。已阅读全部决定与依据，对五项 ENHANCE 深入核验。KEEP 是本轮审计者的保留判断，不构成未发现缺陷的普遍证明。

外部证据重新计算为 55 次成功来源观察，去重后 54 个文件/页面、1,492,456 bytes；其中固定仓库 19 个、固定仓库文件 48 个、官方网页 6 个。完整/部分阅读声明分别为 30 / 24；完整阅读区间与 EOF 相符，具体外部区间与字节偏移相符。所有本地快照 SHA256、字节数和提供的 Git blob 摘要一致。1 次不可用 LICENSE 路径仍保留且标明替代文件。

阅读范围只能审查声明的一致性。独立审查不可能通过哈希重放另一位审计者的实际阅读；本审查也不宣称已独立全文语义复审全部 153 文件。阶段一完整语义阅读的是规则/合同、65 项决定、五项发现、八个直接相关基线文本和四个原探针脚本；其余本地及外部文件执行身份/范围核验。整合清单对这一区别的说明准确。

## 独立反例

| 范围 | 独立运行结果 | 能支持的结论 |
|---|---|---|
| F1 扫描回显 | 从精确 baseline 提取 7 条实际 rg 命令；6 条将合成值回显，原有路径扫描 1 条未回显 | 初筛输出真实存在内容泄漏路径；没有读取真实凭据，不证明任意文件名自动脱敏 |
| F2 中断采样 | 显式 130/143、自 SIGINT/SIGTERM 均执行 3 轮，run-2 存在，汇总返回 1；0/1/9/124 普通控制保留原采样行为 | 原 helper 吞并约定中断身份并继续调用；没有证明真实用户 Ctrl-C、父进程或整个 process group 的行为 |
| F3 CMake 身份 | 独立项目使用 701/902；A→B 复用目录后 cache 指 B，编译及运行仍 701；强制重编译仍 701；新 B 目录为 902 | 成功 configure/build 与新 cache 字符串不能证明实际 toolchain 身份；这是 host 方法证据，不是目标 ABI、板端或硬件资格 |
| F4 schema 闭合 | 真实 jsonschema 运行 5 个 schema × 6 输入；子 schema 提前闭合误拒正常输入，旧 draft 忽略现代闭合字段时放过未知字段；现代组合与同层闭合正常控制通过 | 需要按真实 dialect/支持子集选择闭合方式；不声称现有 ADK 生产 validator 已发生该错误 |
| F5 空审核表 | 精确 baseline 的真实 claude-code / opencode 导出均由默认任务包引用该表，均有 5 行空 Evidence / pass | 已导出待填模板初始状态不真实；没有观察到真实 reviewer 或 runtime Gate 因此被绕过 |

原审计 core 的 4 个探针工件和 embedded 的 13 个工件摘要也已独立复核，一致。独立探针保留原始命令、退出码、stdout/stderr、TSV、CMake cache/系统文件/实际编译命令及实际导出内容。

## 官方来源交叉核验及失败

成功读取 CMake 3.31 官方 `CMAKE_<LANG>_COMPILER` 文档和 JSON Schema 官方 object 文档。前者支持编译器在构建树首次配置时初始化且不能原地切换；后者明确同 subschema 的 additionalProperties 限制，以及 2019-09 起的 unevaluatedProperties 组合闭合。

- https://cmake.org/cmake/help/v3.31/variable/CMAKE_LANG_COMPILER.html （实际网页标为 3.31.12；实验二进制为 3.31.6；仅作为语义旁证）
- https://json-schema.org/understanding-json-schema/reference/object （重点 229–305 行）

GNU Bash Exit Status 官方网页读取超时；无 www 变体不可访问。两个固定 commit 的 raw.githubusercontent.com 文档重新读取被工具拒绝（DisabledError）。这些失败保留，不把本次网页核验说成完整远端 Git tree 重鉴证。全部外部快照的本地摘要核对成功，与远端 membership 证明分开记录；原始来源报告已保留各自固定 URL 和取得方式。

## 后续审查与限制

等待父线程提供 frozen commit/tree、完整 diff、修复后定向验证、全量回归/原预算、真实消费者输入输出及其源码身份。收到后按需求 F1–F5 审查全部补丁，并给独立 Spec 与 Quality 最终裁决；若有实质问题，提供缺陷、反例和修复 task，不修改实现。

授权摘要与 policy 绑定一致；source-only 例外保留。宿主 `~/codex`、native discovery/load/trigger、模型 A/B、付费模型、设备/HIL/现场、Token/成本改进均为未运行/未测量，不从本报告继承任何通过状态。

## 原始证据

- 独立 runner：`/workspace/scratch/fe5385ca063a/round3-independent-stage1-probe.py`
- 独立总回执：`/workspace/scratch/fe5385ca063a/round3-independent-stage1/summary.json`
- 全量身份和范围核验：`/workspace/scratch/fe5385ca063a/round3-independent-stage1/audit-identity-verification.json`
- F1–F5 原始回执分别为同目录的 `scan-original-failure.json`、`sampling-original-failure.json`、`cmake-original-failure.json`、`schema-original-failure.json`、`checklist-original-failure.json`。
- 总回执 SHA256：`9f8fd0c10eed9fad48013c3e1ce7d225078412233cebf185d9e37316af6483e9`。
