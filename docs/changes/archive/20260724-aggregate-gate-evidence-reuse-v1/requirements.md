# 需求基线：aggregate-gate-evidence-reuse-v1

## R1：单次聚合运行内复用
- `scripts/check-all.sh --full` 已成功执行的检查，可以向同一父进程随后启动的
  `check-workspace-entrypoints.sh` 提供只读证据。
- 复用只对显式 allowlist 生效；本次 allowlist 为：
  - `runtime_target_evidence_index` ← `check-runtime-target-evidence-index.sh`
  - `runtime_target_evidence_package` ← `check-root-regression.sh` 中同名 PASS
  - `runtime_target_evidence_promotion` ← `check-root-regression.sh` 中同名 PASS
  - `stale_references` ← `check-stale-references.sh`
  - `pilot_evidence_wrapper` ← `check-runtime-pilot-evidence.sh`
  - `pilot_coverage_wrapper` ← `check-runtime-pilot-coverage.sh`

## R2：fail-closed 真实性绑定
- 证据必须同时绑定 schema、可信父 PID、真实 workspace root、workspace
  fingerprint、producer check 名称与路径、producer 脚本 SHA-256、退出码、
  输出 SHA-256。
- workspace fingerprint 至少覆盖根仓和 `agent-dev-kit` 的 HEAD、tracked
  diff、status 与 untracked regular-file content；不把纯路径相同视为内容相同。
- `check-root-regression.sh` 的子测试复用必须额外验证精确 PASS marker，避免
  “runner 通过但目标测试未被发现”。
- 任一字段缺失、不匹配、证据失败、输出被替换、脚本变化、工作区漂移或
  producer 不是当前父进程时，不报假阳性，自动执行原命令。

## R3：兼容与覆盖不退化
- `check-workspace-entrypoints.sh` 独立运行时不使用复用，仍执行全部原命令。
- `--quick`、`--smoke`、`--verbose`、失败日志和既有 exit-code 语义保持兼容。
- 不复用 `check-adk-harden-readiness.sh`、`check-adk-performance-ops.sh`、
  expected-failure 检查、JSON interface assertions、外部/live 证据或失败结果。
- 不持久化跨会话 cache，不把本次证据用作 release/source-to-live 证据。

## R4：可观测与性能验收
- `check-all --result-json` 记录本次实际复用项；人类汇总能看到复用数量。
- 实际复用项由父进程预建的 owner-only report 记录，不从子命令 stdout 猜测。
- 新鲜 full 至少实际复用上述 6 个 workspace entrypoints，其中两个慢测试
  由 root regression 的同次 PASS 证据覆盖。
- 相对 2026-07-23 基线：
  - full：906 秒；
  - workspace aggregate：207 秒；
  - 两个重复 runtime evidence tests：约 56 秒。
- 验收以覆盖等价为前提：workspace aggregate 目标不高于 165 秒，或在环境
  抖动时提供逐项 timing 证明重复的两个慢测试已不再二次执行。

## R5：负面与回退验证
- 自动测试至少覆盖：合法复用、producer PID 错误、root 错误、失败证据、
  output 篡改、producer 脚本变化、workspace fingerprint 漂移、证据缺失。
- 每个无效场景必须返回“不可复用”，由调用者走原始 `run_check`，不能直接
  把 workspace aggregate 判失败，也不能绕过原命令。

## 阻塞与停止条件
- 同一根因 retry budget 为 2；第三次前 replan。
- 若安全绑定的 fingerprint 成本抵消主要收益，停止扩大复用范围并保留
  独立执行。
- 本 change 的完成条件是定向测试、root regression、ADK gate、新鲜 full
  和独立复审均无 blocker/major；dirty ADK 引发的真实性门禁失败须原样保留。
