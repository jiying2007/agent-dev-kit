# ADK PR #235 — 9.0.0 独立 AI 源码复审

审核时间 UTC：2026-11-04T03:16:00.487Z。Reviewer: `ai/chatgpt/adk235-independent-source-20261104`（独立 AI；非真人、非 Owner、非 GitHub APPROVE 或发布批准）。实现 GitHub 归属账号：`jiying2007`。

- Base SHA: `573452b0ac07dc5464469f09b6825183b2ada6ae`；implementation HEAD: `01a9e7eeda46dabcf784c010713eade75fcc9b01`
- 逐文件核对原生 GitHub 55/55 changed-file patch、351 additions/345 deletions，未依赖实施者陈述。
- Immutable compare: https://github.com/jiying2007/agent-dev-kit/compare/573452b0ac07dc5464469f09b6825183b2ada6ae...01a9e7eeda46dabcf784c010713eade75fcc9b01
- 本次仅作**源码层** Spec PASS / Quality PASS。签发本记录并不构成当前 CI PASS、target-native runtime、现场 Product M5 或正式发布授权。

## 七维源码审查

context_legibility：根 AGENTS/README 说明 build/control plane 与纯 Skill runtime 界线。spec_and_execution_contract：9.0.0 破坏性契约有 requirements/design/tasks 和 Python 3.11 下限。tool_and_permission_boundary：保留权限和受控工具边界；无 MCP 配置的维度结果可为 not-applicable。state_and_knowledge_continuity：保留既有 state、runbook、version lock 与历史不可变记录。verification_review_and_eval：保留完整原生矩阵、静态、供应链、七维 source bound review；本次必须另跑 evidence-only CI。recovery_and_rollback：不触及 8.2.3 release 与 Root pin，保留回滚 runbook。freshness_and_entropy_control：所有来源字节重新计算 SHA256，治理/测试门禁不降级。

## 逐项源行为核对

1. 上轮 Major M1 已修复：`pyproject.toml` 不再有 Ruff UP017 per-file-ignore；`review_evidence.py` 使用 Python3.11 原生 `datetime.UTC`，无需豁免。Ruff、mypy、pip-audit 门禁保留。
2. `requires-python >=3.11`，CI contract+regression Python3.11/3.12；`ADK_PYTHON_BIN` > 激活的 `VIRTUAL_ENV/bin/python` > host auto；低于 3.11、旧/残缺 venv 拒绝执行。相关 shell 负例覆盖。删除兼容模块、旧条件依赖、Bullseye 3.8 Docker 及 py38 专属性能预算。
3. `dataclass(frozen=True, slots=True)` 与 Python3.11 旧 helper 分支语义一致；`hashlib.file_digest` 延续流字节 SHA256，需继续由测试证明。Bundle 静态结构不包含 ADK Python 源码/.py/venv；静态检查不能等同 Claude/Codex/OpenCode 本地原生功能验收。
4. 新 promotion-evidence/v2 规范：canonical schema 与 packaged schema 相同，registry/producer 两路 matrix 为 [3.11,3.12]，旧三版本 v1 数据通过负例拒绝；change archive provenance 权威为 v2。8.x 的历史 v1 review/Release 未更改。Root llm_agent 尚消费旧 v1，必须待真实 signed v9 release 后另走受保护迁移。
5. SHA-pin GitHub Actions、最小权限、原生全矩阵聚合的 fail-closed、CodeQL、dependency-review、platform 和 branch-gc 没有放宽。工具或平台不可达时不允许以本地模拟替代原生结果。
6. 实测 native run `41759300320`：contract-py3.11/3.12、static-security PASS；regression-py3.11/3.12 均 **100/101**，仅 `test_harness_readiness` 因旧 8.2.3 source digest 不符 FAIL，故 deterministic-eval-package 依其失败聚合为 FAIL，promotion-evidence SKIP，不能冒充已达 101/101。CodeQL `41759300334`、dependency `41759300309`、platform `41759300456`、branch GC `41759300469`、Claude `41759300294`、Codex `41759300432`、Digital Worker `41759300349` 均为 success。
7. 性能预算为 report-only；未进行现场、多 host、真实用户设备、模型 provider 或 Product M5 测试。无需也未使用 Codex CLI/Cloud、Work、收费模型。GitHub source review 身份声明无法被文件 SHA256 密码学验证，亦非正式 GitHub APPROVE。
8. 新证据应仅作为 9.0.0 Harness source-bound 输入；下一次 exact evidence-only HEAD 原生完整 CI 和七维 gate 若有意外失败必须继续 HOLD，不得合并或发布。

## Findings

- M1 (major/fixed): 去除 `pyproject.toml` Ruff UP017 豁免，`review_evidence.py` 转为 `datetime.UTC`。
- F2 (minor/accepted-risk): implementation HEAD 两路 100/101 属旧 review digest bootstrap，非 101/101；新 commit 必须重新 CI。
- F3 (minor/accepted-risk): Root llm_agent v1 消费迁移未完成，须 release 后独立受保护处理。
- F4 (minor/accepted-risk): 纯 bundle 静态无 ADK Python 不证明 native runtime、业务效果、现场或 M5。

本报告为新写独立 AI 审核意见；未复制 8.x 证书，也未修改实现源码、CI/Ruff 阈值或旧审核记录。
