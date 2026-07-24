# 评审报告：field-evidence-v2

- 时间：2026-07-23T02:25:50Z
- 执行人：leiwenjun
- 结果：pass
- 分级统计：blocker=0 major=0 minor=0

## 必改项（blocker/major）
- 无未闭环 blocker/major。

## 可延期项（minor）
- 无可延期 minor。

## 问题真实性与证据
- 问题是否可复现：是。post-hoc selection、零分钟 baseline 和错误 module provenance 在修复前可绕过预期语义，已增加负例。
- 证据链接（日志/命令/报告）：根仓 `tests/test_software_m5_certification.sh`、`verify-report.md`。

| ID | 初始级别 | 发现 | 修复 | 复审状态 |
|---|---|---|---|---|
| FIELD-1 | major | 任务预注册未强制发生在 baseline/workload 之前 | 要求唯一 selection/baseline 且 selection ≤ baseline ≤ first workload | fixed |
| FIELD-2 | major | human baseline、wall/agent time 可为 0 | 将必要测量最小值提升为 0.01 并增加零 baseline 负例 | fixed |
| FIELD-3 | major | Python module cache 可能令 M5 使用非受信 certifier | 核验 model/certifier `__file__` 均位于受信 ADK source root | fixed |

## Core/Optional 归属复核
- 归属：core validator + project-bound field evidence。
- 复核结论与依据：校验语义属于 core；operator、repository、时间与 reviewer evidence 必须由项目现场产生，本次未伪造。

- Re-review Result：Software M5 定向测试、full 56/56 与产品成熟度 contract 通过。
- Final Verdict：pass。
