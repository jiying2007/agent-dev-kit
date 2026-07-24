# 设计说明：repository-runtime-evidence-v1

## 架构影响
- 新增 `src/agent_dev_kit/repository_evaluation.py`，只负责 contract/task/report 的确定性校验和认证，不执行外部 Agent。
- `devkit.sh eval repository plan` 读取 contract 与冻结 task metadata，输出 capability、预算和执行边界。
- `devkit.sh eval repository certify --report <path>` 重算 contract/task digest，并验证完整 result matrix、isolation、outcome、process、trace 与 resource evidence。
- 现有 `campaign.py` 和 `software_m5_eval_contract*.json` 保持路由评测语义，不被复用为仓库 runner。
- 根仓 Software M5 增加独立 `repository_runtime_campaign` blocker；缺真实 report 时保持 blocked。

## 数据与配置影响
- 新增 `manifests/repository_runtime_eval_contract.json`，schema 为 `adk-repository-runtime-eval-contract/v1`。
- 新增冻结 task metadata JSONL；每条必须包含 task family、language、os、source kind、revision/digest、freshness、license review、functional/security oracle 类型和 external execution 状态。
- adapter 只允许 `contract-only | available`，默认 `enabled=false`；Inspect SWE 记录版本策略、sandbox、network、credential、trace 和 rollback 边界。
- report schema 为 `adk-repository-runtime-eval-report/v1`。结果矩阵键为 `task_id/runtime/condition/trial`，不得重复或缺失。
- outcome 必须先通过 functional oracle，再判 security；过程指标必须包含 regression cycle、blind retry、final verification、phase order 和 repeated call without evidence。
- resource 必须含 input/output/cached/total token、cost、elapsed、attempt/tool-call/timeout；certifier 计算 p50/p95/max、cost-per-success 和 trial variation。

## 兼容性与迁移方案
- 纯新增 CLI 与 manifest，不改变现有公开命令。
- root M5 只新增 blocker，不把 fixture report 计入真实认证。
- 未提供可审计 customization isolation 的 runtime 返回 `not-comparable`，不会造成 baseline/adk 虚假比较。
- 回滚时移除新模块/CLI/manifest/task/test 和 root blocker；旧 campaign 证据继续有效。

## 验证策略
- `rtk bash tests/test_repository_runtime_evidence.sh`
- `rtk bash scripts/devkit.sh eval repository plan --contract manifests/repository_runtime_eval_contract.json --summary-json`
- 使用临时生成的完整报告验证 certify pass。
- 逐一验证 missing isolation、lucky pass、功能失败、安全失败、token/cost 缺失、digest 漂移和矩阵不完整负例。
- `rtk bash tests/run_all.sh --quick`
- `rtk bash tests/run_all.sh --timing-json <evidence>`
