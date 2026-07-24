# 复审发现：aggregate-gate-evidence-reuse-v1

- Review Scope：根 `check-all` producer、workspace consumer、same-run evidence
  helper、contract tests 与本 change 工件。
- Requirement Baseline：`requirements.md` R1-R5；优化只允许同父进程、同一未
  变化 workspace 的 allowlist PASS evidence，invalid evidence 必须 fallback。
- Verification Baseline：root 17/17；shellcheck PASS；最终 fresh full
  55/59、854 秒、reuse 6、workspace 151 秒。

## Findings

| ID | Severity | File | Evidence | Required Action | Status |
|---|---|---|---|---|---|
| CR-001 | minor | `scripts/check-all.sh` | 初版从 workspace stdout 解析 `[REUSE]`，失败命令输出同格式文本可能污染性能计数 | 使用父进程预建 600 report；append 失败 fallback；加入 stdout spoof fixture | fixed；contract test PASS |
| CR-002 | question | `scripts/lib/same-run-evidence.sh` | 是否应防御拥有 workspace 写权限且控制父进程的恶意本地用户 | 对照权限模型后确认该主体可直接修改 gate 源码，不属于本机制可提供的隔离边界 | documented；not-a-defect |

## 异常与安全分支核验

- failed producer、错误 PID/start token/root、缺失 marker、output/script digest
  漂移、tracked/untracked/ADK fingerprint 漂移、metadata symlink 和 evidence
  缺失均被 validator 拒绝。
- report 必须与 evidence 同级、owner-owned、非 symlink、非 group/world
  writable；append 失败时 consumer 执行原始 `run_check`。
- internal evidence variables 在 workspace consumer 中取消 export，不传递给
  后续 leaf commands。
- standalone、quick、smoke 不获得 evidence；standalone 实测完整执行且没有
  `[REUSE]`。

## False Positives

- full 的 current-status、evidence-bundle、subrepo-state、workspace 四个失败
  不是本 change 的四个独立缺陷；它们仍由 strict ADK working tree dirty
  派生，且与优化前失败集合完全一致。为其建立 dirty baseline 会掩盖交付边界。
- 首轮 harden 失败来自前一 change 评审文档写入外部参考仓名；按 ADK 交付
  资产规则泛化后，定向 external-reference test 与两次完整 harden 均 PASS。

## Out-of-scope Suggestions

- token budget 和 governance JSON entrypoints 仍存在可观测重复，但没有本次
  allowlist 所需的等价 producer output contract；继续复用会扩大 schema 与
  coverage 风险，暂不纳入。
- 恶意同 UID 进程隔离需要 OS sandbox/独立凭证，不由本地 Bash gate cache
  解决。

## Fix Plan 与复审

- CR-001 已以专用 report 和 stdout-spoof integration fixture 最小修复。
- CR-002 已写入 design 的 threat model，不放宽 evidence 校验。
- Re-review Result：blocker=0、open major=0、open minor=0、question=0。
- Final Verdict：source review pass；delivery 仍受 strict ADK dirty 和未授权
  Git/source-to-live 动作约束。
