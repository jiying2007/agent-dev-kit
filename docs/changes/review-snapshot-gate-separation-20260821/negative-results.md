# Negative Results

## 2026-08-21 upstream regression

- `rtk scripts/devkit.sh validate --quick`：通过；环境提示 Python 3.8.10 仅可作为开发证据。
- `rtk tests/test_skill_sop_quality.sh`：本次新增的 snapshot、overlay、independence 和 gate 文本断言通过，随后被既有 `github-gh-aw-safe-outputs`、`mcp-registry`、`otel-genai-semconv` source_ref 审查过期阻断。
- `rtk tests/run_all.sh --fail-fast`：在 `test_validate` 被相同的三个既有 source_ref 过期项阻断，未进入后续测试。

这些 source_ref 不属于本 change 范围，未通过放宽门禁或修改到期记录规避失败。
