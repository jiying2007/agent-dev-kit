# 验证报告：adk-v3-1-rc2-target-conformance

- 验证时间：2026-07-13T15:31:22Z
- claimant：Codex
- verifier：`adk-verification-before-completion`
- 结论：本地实现与 source/test 控制面通过；release promotion、direct target runtime 认证和 field certification 仍被明确阻断。

## 核心结果

| 验证面 | 结果 | 关键证据 |
|---|---|---|
| Manifest / assets | PASS | strict validation；12 agents、56 skills、9 optional skills、9 profiles、6 workflows |
| ADK full regression | PASS | 51/51 |
| Target static contracts | PASS | Claude Code/OpenCode/Hermes 3/3；三者分别检查 97、97、85 个 rendered files |
| Target runtime smoke | NOT-RUN | 三个 target discovery 均 `not-certified`、exit 2；未提供真实只读 runtime harness |
| Official docs freshness | PASS | 69 条；OpenAI 最低 64、Anthropic 最低 5；域名归属和 90 天窗口受控 |
| Effect eval | PASS | 24/24；route/safety/trace/outcome 均 1.0；routing-disabled 0.6667，delta 0.3333，高于 0.1 gate |
| Performance | PASS | 7 个 latency/I/O budget 与 peak-memory gate 全通过 |
| Static/security | PASS | Ruff 0.15.21、ShellCheck、内建 security、兼容版 pip-audit 2.7.3 |
| Release control plane | PASS | version/target/workflow/SBOM/provenance static contract check |
| Root quick integration | BOUNDARY FAIL | 52/56；4 项均由未提交 rc.2 与根仓 rc.1 gitlink/lock 基线不一致触发 |

## 性能证据

五次采样的 p95：manifest strict 192.748 ms、profile resolve 5.412 ms、export plan 83.825 ms、target static 223.881 ms、CLI cold-start 502.553 ms、10x plan 904.996 ms、10x filesystem I/O 998.409 ms。10x plan peak allocation 为 272.385 KiB，低于 8,192 KiB gate；I/O 样本为 400 files、1,809,710 bytes。所有预算均通过，详见 `benchmark.json`。

## 负证据与声明边界

1. 本机检测到 Claude Code 2.1.138，但没有执行登录、付费 prompt 或 live target 写入；CLI 存在不能替代 discovery/load/trigger 认证。
2. OpenCode 与 Hermes runtime 不存在；三者真实 smoke 都保持 `not-run`，因此 direct targets 继续为 `experimental`。
3. 根仓 `adk.lock` 和 gitlink 保持 `3.1.0-rc.1`。在 rc.2 尚无真实 commit 时更新 lock 会制造不可重现证据，因此 4 个根仓门禁失败是预期且正确的阻断行为。
4. 本机 Python 3.8 无法运行 CI 固定的 `pip-audit==2.10.1`；本地仅以兼容版 2.7.3 补充审计。GitHub workflow 已固定 Python 3.12 + 2.10.1，尚待远端执行。
5. 该报告只证明 source/test 与本地 integration 层；不证明 runtime、remote CI、attestation backend、第二操作者或 field 层。

## Release rehearsal

最终 reproducible build 和 rc.1 → rc.2 rollback-before-install 演练结果写入同目录 `release-rehearsal.json`。演练还会从保留的 rc.1 artifact 重装并逐文件比对 managed hashes，再清理临时 target。该运行态文件被 source distribution 明确排除，以避免制品 digest 与自引用验证报告形成循环。

## 后续提升条件

- 用户授权并创建 ADK commit 后，更新根仓 gitlink、`adk.lock`、current-status 和 Software M5 integrity，再重跑根仓 full。
- 在隔离测试根目录中，用真实 runtime harness 分别完成 discovery、load、trigger、permission 四阶段并保存不可变 evidence。
- 远端运行 clean-clone CI、OpenSSF Scorecard 和 GitHub artifact attestation。
- 按 Software M5 policy 完成双 runtime campaign、独立仓库、第二操作者、真实仓库数量和 30 天观察。
