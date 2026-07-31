# RC6 release baseline verification

## Scope Summary

- release source commit：`9f82e1d9deffadc3967f446069375f5872363d46`
- previous artifact：checksum-bound `3.1.0-rc.5`
- candidate artifact：exact-commit `3.1.0-rc.6`
- source-to-live：`required-pending-owner-authorization`
- excluded：live apply、tag、remote release、runtime campaign、field certification

## Verification Results

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk scripts/check-change-governance.sh docs/changes/rc6-release-baseline-refresh-2026-07-31` | 0 | change 工件与边界完整 | command output | Workflow | T1 |
| `rtk scripts/devkit.sh validate --strict` | 0 | RC6 manifest 与资产 strict pass | command output | Source | T1 |
| `rtk scripts/devkit.sh release check --summary-json` | 0 | version `3.1.0-rc.6`，failures 为空 | command output | Release | T1 |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full`（首轮） | 1 | 两套环境均 56/57，reference residue gate 命中 | `negative-results.md` | Test | T2 negative |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full`（修复后） | 0 | Python 3.11/3.12 均 57/57；audit 无已知漏洞 | command output | Test/Release | T2 |
| exact commit 双 `release build` + `cmp` + checksum | 0 | 720 source files；两份 artifact SHA256 均为 `4cd728126b7242150665315a22706811c12de4de9f136eaef17b0e3ecbe63b15` | `/tmp/adk-rc6-release.3ERZOJ/` | Release Artifact | T3 |
| RC5→RC6 `release rehearse` | 0 | 39→39 原位升级；rollback removed/restored=39；RC5 hashes 恢复 | `release-rehearsal.json` | Release Runtime | T4 |
| `rtk scripts/check-all.sh --full` | 0 | 根仓 60/60，`check-current-status-consistency` 与全部聚合门禁通过 | root command output | Project/Release | T6 |

## Completion Claim Audit

- claimant：Codex 声明 RC6 source 和本地 release baseline 已验证。
- verifier：命令级证据支持版本、支持 Python、artifact reproducibility 和 rollback rehearsal。
- 不支持的声明：live applied、runtime certified、M5 certified、remote release published、final release ready。

## Compatibility and Rollback

- breaking change：无新增 API 删除；RC6 封装 RC5 后映射资产变更。
- migration：见 `docs/migrations/3.1.0-rc.6.md`。
- rollback：checksum-bound RC5 artifact；rehearsal 已证明 managed hashes 可恢复。
- live rollback：本次未 apply，因此不产生或冒充 live backup anchor。

## Gate Result

ADK source/release evidence与根仓 policy/current-status/full gate：`pass`。source-to-live 保持 `required-pending-owner-authorization`。

## Final Closeout

- root full：60/60 pass。
- final-ready：pass。
- publication scope：仅 source commit push；无 tag、remote release 或 artifact upload。
- residual boundary：source-to-live、runtime campaign、field certification 继续独立授权与取证。
