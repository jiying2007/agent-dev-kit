# 审查更正记录（追加，不替换封存证据）

日期：2026-11-17 UTC。适用：context/optional 20项独立首轮审查。

## 导出覆盖概括更正

首份报告错误地把 `core + 9 optional` 的导出概括为20/20。原 `probe-results.json` 从生成起就正确记录 **16/20**，以下4项 `selected_skill_presence=false`：

- `adk-planning-execution-loop`
- `adk-memory-curator`
- `adk-archive-governance`
- `adk-knowledge-archive`

这4项不属于所选 core profile；不是编译器丢文件。新增测试首轮也误用了 core，导致3个测试入口错误；首次 `implementation/red-tests.log` 保留，不把这些错误当产品RED。

在实施 Skill 修改前，使用既有 `team-core + 9 optional` 做追加对照，Claude Code/OpenCode 两个实际导出都覆盖20/20。没有改变任何 profile：

- 入口：`verify_team_export.py`
- 结果：`export-coverage-control.json`
- 实物：`fixtures/team-exports/{claude-code,opencode}/`
- 两个导出的 `adk-export-manifest.json` 都绑定 Manifest 11.3.13，digest `8fc37332a821e65fc83267c0dd113a6760d6c55a8d48b1a7ff8b7082c184a3d1`。
- 将测试夹具切到 team-core 后，未修改 Skill 的有效RED为 `implementation/red-tests-valid-profile.log`：5项测试、11个失败、0个错误。

修正后的 `report.md` 及 `coverage.json` 明确区分初始16/20与追加20/20；原 probe、原封存报告和首次日志均不覆盖。原始两个 source-helper exit127 反例仍有效，因为涉及的两个 optional Skill 原本就在16项中。

## v2 字段计数更正

parallel 人类信封为25字段，与canonical19字段重叠8个。直接转换有 **11个缺失字段、17个额外字段**。早期消息把额外字段说成18，属于人工计数错误；`contract-edge-results.json` 原始字段列表一直正确，未改变 validator 或原始结果。

## 修正版本指纹

| 文件 | SHA-256 |
|---|---|
| 修正后的 report.md | `ef458acadceb034c8afa8586263aded1669d2e9d1282fcfdd6a143a21dcd655a` |
| 修正后的 coverage.json | `ef0723032a6ebce1d81e29156a4467b07e0b8ea3de14941e1eb024e583c30520` |
| 新增 export-coverage-control.json | `15135c022d114d031e3922a464d7deb1d8865cacb3cfb9466b8b1b5610148bfb` |
| 未改的 probe-results.json | `119424d0969b8e69984d5c3252e02a84b357bbda5ebcdab26813463f07b81020` |
| 未改的 contract-edge-results.json | `71d22167648413649fb9ec2a0ee92c1cef1e4bb36bb2eec5199c9a74cb1c0d73` |

这些更正不增加真实模型、原生宿主、外部服务或Token收益的证据级别；相关状态仍为 not-measured。
