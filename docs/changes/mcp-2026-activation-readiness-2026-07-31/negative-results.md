# 负结果：mcp-2026-activation-readiness-2026-07-31

## 已验证的负结果

| Date | Assumption / path | Experiment | Result | Decision |
|---|---|---|---|---|
| 2026-07-31 | 可用可变 latest SDK 代表 final compatibility | 检查官方 SDK release | Go SDK 当前目标版本为 pre-release；latest 语义不稳定 | 固定 `v1.7.0-pre.3`、tag commit 与 module sum |
| 2026-07-31 | host Go 可直接执行 fixture | 环境 inventory | host 无 Go | 固定 Docker image digest |
| 2026-07-31 | metadata final/rollback 可代替 runtime smoke | Hub exact-source 审计与 contract review | 无法证明 wire 行为 | 必须执行真实 SDK loopback 和 legacy fallback |
| 2026-07-31 | 只挂载 `GOMODCACHE` 足以在只读容器准备依赖 | 首轮 `go mod tidy` | sumdb 仍写默认 `/go/pkg/sumdb` 并失败 | 显式挂载完整 `GOPATH`，同时约束 module 与 sumdb cache |
| 2026-07-31 | `go mod download all` 在只读 fixture 上不会改 sum | 首轮 `--prepare` | Go 尝试补写未参与 build list 的 checksum | 改为按 `go.mod/go.sum` build list 执行 `go mod download` |
| 2026-07-31 | 64 MiB tmpfs 足够 Go 1.25 首次 test workdir | 首轮 `--offline` | 编译中 `$WORK` 空间耗尽，行为测试未开始 | tmpfs 提升为 1 GiB；module/build cache 仍在显式 `/tmp` |
| 2026-07-31 | test workdir 可使用 `noexec` tmpfs | 第二轮 `--offline` | Go test binary 无法执行 | 仅移除 `/tmp` 的 `noexec`；保留 read-only root、nosuid 与 network=none |
| 2026-07-31 | Docker `--tmpfs` 可通过省略 `noexec` 获得 exec | mount 只读取证 | daemon 仍强制 `/tmp` 为 `noexec` | 设置 `GOTMPDIR` 到显式 host bind build cache；`/tmp` 恢复小型 noexec tmpfs |
| 2026-07-31 | invalid output 一定以 `CallToolResult.IsError` 返回 | 首次行为级 offline run | SDK 以包含 `validating tool output` 的 protocol error 拒绝 | 接受该明确 fail-closed 通道，并校验错误定位到 integer schema |
| 2026-07-31 | legacy handler 必须以非 2xx 拒绝 `server/discover` | 首次行为级 rollback run | handler 返回 200，但 supportedVersions 只含 legacy；SDK client 已回退到 `2025-11-25` | 固化协商语义，并追加 modern `tools/list` 必须失败 |
| 2026-07-31 | 形如 `fixture-valid-token` 的合成值不会触发 secret scanner | 首轮双 Python full parity | `quality.SECRET_CONTENT` 按 token assignment + 16 字符匹配，阻断 product maturity | 缩短所有 opaque 合成 bearer 值；保留完整 auth 负例语义 |

## Evidence Index（命令级）

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk scripts/check-change-governance.sh docs/changes/mcp-2026-activation-readiness-2026-07-31` | 1 | tasks 标题未使用 checker 要求的“Ownership 与并行冲突检查”精确名称 | 本文件 | Change | T0 |
| 同上（第二轮） | 1 | tasks 缺少“轻量工件与收敛结论” | 本文件 | Change | T0 |
| 同上（第三轮） | 1 | negative-results 缺少 checker 要求的精确 section/table contract | 本文件 | Change | T0 |
| 同上（第四轮） | 1 | checklist 缺少 Prompt before/after 精确检查项 | 本文件 | Change | T0 |
| 同上（第五轮） | 1 | checklist 检查项必须与 checker 文本完全相等，不能追加说明 | 本文件 | Change | T0 |
| `rtk docker run ... go mod tidy`（首轮） | 1 | 只读容器的默认 `/go/pkg/sumdb` 不可写 | 本文件 | Dependency | T2 |
| `rtk scripts/check-mcp-2026-activation.sh --prepare`（首轮） | 1 | `download all` 尝试更新只读 go.sum | 本文件 | Dependency | T2 |
| `rtk scripts/check-mcp-2026-activation.sh --offline`（首轮） | 1 | 64 MiB tmpfs 空间不足，Go build 未进入用例 | `/tmp/adk-mcp-2026-activation-go-test.jsonl` | Environment | T1 |
| 同上（第二轮） | 1 | `/tmp` noexec 阻止 Go test binary 启动 | `/tmp/adk-mcp-2026-activation-go-test.jsonl` | Environment | T1 |
| 同上（第三轮） | 1 | Docker daemon 仍把 `/tmp` 挂载为 noexec | `/tmp/adk-mcp-2026-activation-go-test.jsonl` | Environment | T1 |
| `rtk docker run ... mount` | 0 | 确认 `/tmp` 实际选项含 `noexec` | 本文件 | Environment | T1 replan |
| `rtk scripts/check-mcp-2026-activation.sh --offline`（行为红灯） | 1 | client/server 与 auth 通过；schema error channel、rollback discover 语义与初始假设不同 | `/tmp/adk-mcp-2026-activation-go-test.jsonl` | L2 | T1-T3 |
| 同上（rollback 响应形态） | 1 | modern tools/list 已以 HTTP 400 plain text 正确拒绝；测试错误地先按 JSON 解码 | `/tmp/adk-mcp-2026-activation-go-test.jsonl` | L2 | T3 |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full`（首轮） | 1/terminated after repeated failure | Python 3.11、3.12 均发现新 fixture credential-like literal；其余已运行门禁通过 | parity terminal evidence | Release | T5 |
| `rtk scripts/check-agent-ecosystem-standards.sh --summary-json`（decision schema 首轮） | 1 | checker 调用未定义 `load()`，在 decision schema 断言前退出 | command output | Static gate | T5 |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full`（decision request 首轮） | 1/terminated after Python 3.11 result | ADK verify report 写入外部参考仓名称，被 no-external-repo-refs 门禁拒绝 | parity terminal evidence | Release | T5 |
| `rtk scripts/check-mcp-2026-activation.sh --offline`（ACTIVATE 状态迁移首轮） | 1 | 四项 Go 测试通过；wrapper 仍断言 owner pending，阻断新状态 | `/tmp/adk-mcp-2026-activation-go-test.jsonl` | L2/State | T7 |
| `rtk scripts/check-agent-ecosystem-standards.sh --summary-json` | 0 | 527 checks、13 negative fixtures、runtime disabled | command output | Static gate | T4-T5 |
| `rtk tests/test_agent_ecosystem_standards.sh` | 0 | ecosystem 正负 fixture 回归通过 | command output | L1/L2 | T4-T5 |
| `rtk scripts/check-mcp-2026-activation.sh --offline` | 0 | schema/client-server/auth/rollback、owner record 和 governance activation 状态通过 | `/tmp/adk-mcp-2026-activation-go-test.jsonl` | L2/State | T1-T7 |
| `rtk scripts/check-change-governance.sh docs/changes/mcp-2026-activation-readiness-2026-07-31` | 0 | change governance 通过 | command output | Change | T0-T6 |
| `rtk scripts/devkit.sh validate --strict` | 0 | strict validation 通过；host Python warning 不作为 release 证据 | command output | L1 | T5 |
| `rtk scripts/run-local-ci-parity.sh --python all --mode full`（修复后） | 0 | Python 3.11/3.12 各 57/57，routing 各 30/30，dependency audit 无已知漏洞 | parity terminal evidence | Release | T5 |
| `rtk scripts/check-format.sh` | 0 | format gate 通过 | command output | Static gate | T5 |
| `rtk tests/test_file_modes.sh` | 0 | executable/file mode gate 通过 | command output | Static gate | T5 |
| `rtk tests/test_product_maturity_v3.sh` | 0 | product maturity gate 通过 | command output | Release | T5 |
| `rtk git diff --check` | 0 | 无 whitespace error | command output | Static gate | T5 |
| 根仓 `rtk scripts/check-all.sh --quick` | 1（49/54） | 五项失败归因到过期 reference baseline、stale artifact hash、gitlink/lock 状态和本次合法 dirty | 根仓 command output | Aggregate | T5 |
