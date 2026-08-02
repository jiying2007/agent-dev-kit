# 验证报告：RC7 Token 与上下文治理 release baseline

- 时间：2026-08-02T09:38:02+08:00
- 执行人：Codex
- release source：`60c9a9ebbcc38ebdfcb07bc1fd399f533ce08e5f`
- 版本：`3.1.0-rc.7`
- 结论：ADK release source、可复现 artifact 与本地回滚演练通过；根仓 release-clean 和最终远端对齐由根仓证据继续收口。

## Supported-environment full parity

- `rtk scripts/run-local-ci-parity.sh --python all --mode full`：exit 0。
- Python 3.11.15：58/58 tests pass，dependency audit 无已知漏洞。
- Python 3.12.13：58/58 tests pass，dependency audit 无已知漏洞。
- source snapshot：`c9405c3480a815e545c390ba26b84c96d304facc2c2604882d140cfe7dcb64e9`。
- file-mode inventory：`ac9e0b10058179e08da8dae7bd3e8d9a55cbe839a45bfbd00ac5143e049c4456`。
- Python 3.11 image：`sha256:2f4ec1f0197b789009d2cae4f5288fcf213e2167adf1afa47665f641c2d4c451`。
- Python 3.12 image：`sha256:3fcedbe94b2caf8081d7b509eea6ec5279cc7bb5923622598327a36a713878c8`。

## Exact-source artifact

- 两次 clean build 的 `source_file_count` 均为 754。
- A/B artifact SHA256 均为 `a46d26d79be3ee0bed02cde9c5fa031a5c0cd6e533793edc906b01f753ec48e0`。
- `cmp` exit 0；两份 `.sha256` 均经 `sha256sum -c` 验证为 `OK`。
- 首轮 source `e03898f` 产生的 `38c6a14b…cf59` artifact 已明确废弃，未进入本报告。

## Upgrade 与 rollback rehearsal

- RC6 artifact SHA256：`4cd728126b7242150665315a22706811c12de4de9f136eaef17b0e3ecbe63b15`，预检为 `OK`。
- RC6→RC7 in-place replacement：pass。
- rollback：pass；removed=39、restored=39、restored_assets=39。
- 完整机器可读结果：`release-rehearsal.json`。
- rehearsal launcher 使用宿主 Python 3.8，仅证明安装/回滚功能；release 支持环境判定只采用上面的 Python 3.11/3.12 full parity。

## 内容与治理边界

- `rtk git diff --check origin/main..60c9a9e`：exit 0。
- `rtk git diff --quiet 60c9a9e -- agents skills optional-skills workflows templates`：exit 0，evidence 未改动 mapped runtime assets。
- prompt before/after 证据沿用并复核 `../token-context-workflow-optimization-v1/verification-evidence.md`；本 change 仅固化 release baseline，不引入新的 prompt 语义。
- 未创建 tag、GitHub Release 或远端 artifact；未执行 active knowledge promotion。

## 待根仓收口

- 更新 root `adk.lock`、current status、M5 policy/ledger 与 RC7 release evidence。
- 运行 root `scripts/check-all.sh --release-clean` full gate。
- 复核四仓 upstream、残留 dirty 与授权边界。
