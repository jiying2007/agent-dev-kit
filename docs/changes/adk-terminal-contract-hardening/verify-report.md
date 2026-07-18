# 验证报告：adk-terminal-contract-hardening

- 验证日期：2026-07-18
- 环境：本地 Linux；宿主 Python 3.8.10（不属于新发布支持矩阵）；固定 Docker Python 3.11.15/3.12.13
- 结果：本地实现、RC3 exact-commit 制品与升级回滚 rehearsal 通过；远端 CI/runtime/field 认证阻塞

## 结果摘要

- source quick：17/17，strict budget 120000ms 内。
- RC3 release tree full：54/54，335446ms，strict budget 600000ms 内。
- benchmark：全部 7 个时延 gate 与 peak memory gate 通过；manifest validation p95=99.853ms。
- strict/schema/install/docs/security/release/ShellCheck：通过。
- root performance wrapper：通过。
- root full：父仓 gitlink/policy/evidence 尚待锁定；在父仓闭环前不声明根产品基线通过。
- controlled quick：Python 3.11/3.12 各 17/17；非 root、gates 无网络、audit 独立 bridge。
- controlled full：同一 source snapshot `33ab17d4...` 上 Python 3.11/3.12 各 54/54；performance、security、30/30 eval、release check、wheel 与依赖审计通过。
- RC3 source commit：`defe8a078b9693b6963e434f3131891ebbcf5d62`；两个独立 commit archive build 字节一致，SHA256=`46afbb507f61fce8facffbfa36c23f59fe3f5498e3f1843ceaa53f2507d8fcd8`，source files=576。
- release rehearsal：实际历史 RC2 artifact checksum 有效；rc.2 → rc.3 各安装 39 项，候选回滚恢复 39 项，report SHA256=`1526ac3aaeb275c4c34da79419e2aed9588620c6487ee6b8805232de31096de9`。
- provenance 负证据：RC2 release commit 重建为 520 files，与历史 521-file artifact 不同；唯一额外 source 是忽略的 `history.log`。RC3 构建器已排除 `*.log` 并加归档回归，未篡改 RC2 历史证据。
- review：TC-005～TC-008 修复后 blocker=0、major=0；结论只覆盖本地 source/test 与临时 waiver。

详细命令、退出码、证据层级和剩余边界见 `verification-evidence.md`。
