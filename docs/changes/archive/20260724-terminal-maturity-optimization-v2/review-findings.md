# 复审发现：terminal-maturity-optimization-v2

- Review Scope：本 change 的根仓聚合/测试、成熟度语义、参考仓 baseline、
  ADK Python launcher、workflow retry、CI 与文档；用户既有 Software M5、
  repository runtime、MCP/security dirty 改动只验证共享工作树，不归为本轮作者。
- Requirement Baseline：全面优化 `llm_agent` 与 `agent-dev-kit`，本地实现闭环，
  外部现场、Git 和 live 写入不越权。
- Verification Baseline：ADK 57/57、root 16/16、Python 3.11/3.12 各 20/20、
  fresh full 55/59。

## Findings

| ID | Severity | File | Evidence | Required Action | Status |
|---|---|---|---|---|---|
| TM-001 | major | `manifests/product_maturity_scorecard.json` | D09 改为 `verified_local` 后没有 `gap`，违反新增状态语义 | 补 gap，并要求所有 local/partial 状态带 gap | fixed；双 scorecard 门禁通过 |
| TM-002 | major | `agent-dev-kit/scripts/workflow.sh` | 首次 verify 进入 `verify-failed` 后，原状态机只接受 `applied`，无法在同 change 重试 | 允许从 `verify-failed` 重试，增加失败恢复回归 | fixed；`test_workflow` 与 full 通过 |
| TM-003 | minor | root/ADK aggregate | fresh full 约 15 分钟；harden、performance、root、workspace 是主要耗时项 | 后续基于 timing JSON 设计可验证的 dependency/result reuse，不牺牲唯一覆盖 | fixed；`aggregate-gate-evidence-reuse-v1` 最终 full 854s、workspace 151s、reuse 6，失败集合不变 |

## False Positives

- fresh full 的四个失败不是四个独立代码缺陷：它们都由 strict ADK dirty 状态
  派生。删除检查或为 ADK 建 dirty baseline 都会掩盖真实交付边界，故拒绝。
- 三个 observe 参考仓的 655/115/216 项变化不是本轮意外漂移：fingerprint、
  分类、HEAD 与 commit-snapshot-only 策略全部匹配，已生成当天 report-only
  triage；具体仓名只保留在根仓治理证据，不写入 ADK 交付资产。

## Out-of-scope Suggestions

- `~/codex/scripts/context-preflight.sh --help` 把 `--help` 当输出路径；属于另一个
  源仓，本 change 只保留负证据。
- commit/push、gitlink/adk.lock/current-status 刷新、source-to-live apply 与真实
  runtime/field campaign 需要 owner/外部条件，不以本轮代码修复代替。

## Fix Plan 与复审

- TM-001：最小修改 scorecard/checker/test；定向 maturity 与 architecture tests
  通过，root 16/16 通过。
- TM-002：最小修改 workflow 状态转换、测试与命令文档；ADK 57/57 和双 Python
  quick 通过。
- TM-003：只复用同父进程、同 workspace fingerprint 的 allowlist PASS
  evidence；harden/performance 保持独立执行，invalid evidence 自动 fallback。
- Re-review Result：blocker=0、open major=0、open minor=0。
- Final Verdict：source review pass；delivery/release 仍 blocked，见
  `verify-report.md`。
