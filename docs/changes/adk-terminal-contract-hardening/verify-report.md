# 验证报告：adk-terminal-contract-hardening

- 验证日期：2026-07-18
- 环境：本地 Linux；宿主 Python 3.8.10（不属于新发布支持矩阵）；固定 Docker Python 3.11.15/3.12.13
- 结果：本地实现与受控 CI waiver 替代证据通过，外部/发布证据阻塞

## 结果摘要

- quick：16/16，65331ms，strict budget 120000ms 内。
- full：当前最终树 53/53，340107ms，strict budget 600000ms 内。
- benchmark：全部 7 个时延 gate 与 peak memory gate 通过；manifest validation p95=99.853ms。
- strict/schema/install/docs/security/release/ShellCheck：通过。
- root performance wrapper：通过。
- root full：55/62；失败保留为未提交 candidate/evidence 状态，不影响本地代码回归结论，也阻止 release-ready 声明。
- controlled quick：Python 3.11/3.12 各 17/17；非 root、gates 无网络、audit 独立 bridge。
- controlled full：同一 source snapshot `33ab17d4...` 上 Python 3.11/3.12 各 54/54；performance、security、30/30 eval、release check、wheel 与依赖审计通过。
- review：TC-005～TC-008 修复后 blocker=0、major=0；结论只覆盖本地 source/test 与临时 waiver。

详细命令、退出码、证据层级和剩余边界见 `verification-evidence.md`。
