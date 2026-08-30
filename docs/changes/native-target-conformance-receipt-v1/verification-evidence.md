# Verification Evidence: Native Target Conformance Receipt V1

| Command | Result | Scope |
|---|---|---|
| `rtk tests/test_target_contracts.sh` | pass | target schema、static trust policy、strict receipt 正负 loader、无 verifier synthetic promotion 拒绝 |
| `rtk python3 -m py_compile src/agent_dev_kit/targets.py` | pass | Python syntax |
| `rtk python3 -m json.tool schemas/native-target-conformance-receipt-v1.schema.json` | pass | receipt schema JSON |
| `rtk claude --version` | `2.1.138` | runtime identity preflight |
| `rtk claude auth status` | OAuth 状态报告 logged-in | 仅 preflight；不等于非交互 `claude -p` 可认证 |
| CR7 `claude -p` project skill probes | unknown-command / not-logged-in；3 次均 0 Token、USD 0 | setting-source discovery/auth 负证据；非 stage pass |

Native runtime certification：not-run。首次 discovery 在模型调用前配置失败；合法 empty MCP record 的重试没有合格
structured output；CR7 又分别隔离验证 project discovery 与 OAuth source，仍为 unknown-command/not-logged-in，
所有尝试 API duration/token/cost 为零。以上均不属于 stage pass evidence。

Cryptographic/provenance verification：open。当前 fresh pass 只证明 schema、完整性验证和 fail-closed promotion，不证明外部 authority 身份。
