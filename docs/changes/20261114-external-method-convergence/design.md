# 吸收方式与设计取舍

本轮直接读取 OpenAI/Anthropic、Sentry、Cloudflare、Trail of Bits、Microsoft、NVIDIA、Vercel、Zephyr 等真实 Skill 或 README，按单文件 blob 冻结。见 `docs/evals/external-skill-method-comparison-20261114.md`。

1. `adk-interface-contract-design` 按需 reference 双向核要求与实现，条件性的已有实现才需要；移除貌似生产默认值的硬编码超时/重试示例。
2. `adk-code-review-loop` 在完整 Review 将要求→代码和代码→要求并入已有 coverage ledger，禁止以文件检查数量当缺陷发现率；不扩展为第二套审查工具。
3. `adk-security-supply-chain` 引入目标真实不变量、受影响 principal/source-to-sink 与未扫描范围，区分 confirmed/false-positive/unverified；修复 Workflow 编号重复，保留只读 intake/正式引入分层。
4. `adk-skill-composition-governance` 在既有行为评测 reference 补 Train/Holdout 冻结与防泄漏、同条件重复。新增 9 个现有案例的 source-only 预注册合同（5 train/4 holdout，no-model-runs）。
5. `adk-token-context-governance` 以实际质量安全与运行 Trace 决定 Token 优化优先级，不把 65 个 Skill 的源码字节数当输入费用。

全部新用例追加到已经运行的 `tests/test_skill_quality_methods.py`，不增加 shell test job、MCP 依赖、模型 runner、安装器或额外权限。这些是 E0/E1 声明和负面边界测试，不能宣称更好的真实触发率、性能或安全扫描命中。
