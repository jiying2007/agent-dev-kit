# 评审报告：repository-runtime-evidence-v1

- 时间：2026-07-23T02:25:50Z
- 执行人：leiwenjun
- 结果：pass
- 分级统计：blocker=0 major=0 minor=0

## 必改项（blocker/major）
- 无未闭环 blocker/major。

## 可延期项（minor）
- 无可延期 minor。

## 问题真实性与证据
- 问题是否可复现：是。初审发现的布尔 trial、contract-only 真实认证和不安全 trace ref 均可由构造报告复现，已闭环。
- 证据链接（日志/命令/报告）：`tests/test_repository_runtime_evidence.sh`、`tests/test_software_m5_ready.sh`、`verify-report.md`。

| ID | 初始级别 | 发现 | 修复 | 复审状态 |
|---|---|---|---|---|
| RRE-1 | major | JSON `true` 可与 trial 1 等价进入矩阵 | 显式拒绝 bool/non-int trial，并增加负例 | fixed |
| RRE-2 | major | `contract-only` adapter 可产生真实 `pass` | clean-room 降为 `fixture-pass`；真实 pass 要求 available + SHA-256 version pin | fixed |
| RRE-3 | minor | trace `summary_ref` 未限制为安全相对路径 | 拒绝 absolute 与 `..` 路径 | fixed |

## Core/Optional 归属复核
- 归属：core contract + optional runtime adapter。
- 复核结论与依据：确定性 certifier 属于 core；Inspect SWE、外部容器、网络与凭证仍为 disabled-by-default optional，未安装。

- Re-review Result：full 56/56，strict 与定向负例通过。
- Final Verdict：pass。
