# 设计说明：adk-v3-1-software-m5-ready

## 架构影响
- `campaign.py` 增加 campaign plan/run/check/certify，逐任务结果原子落盘并支持 resume；`evaluation.py` 保留单次 runtime 与 deterministic 执行能力。
- 新增 writer lock 模块，export/apply/rollback 共享 target 互斥契约；plan/dry-run 保持只读。
- `release.py` 增加 local artifact rehearsal，验证升级、故障回退和 receipt，不增加远端 backend。
- CLI 增加 `doctor`、`lock`、`eval campaign/certify`、`release rehearse`。

## 数据与配置影响
- 产品版本升级到 `3.1.0-rc.1`。
- campaign contract 固定 runtimes、conditions、trials、suite hash、预算与门禁；结果记录 model/CLI、latency、token/cost、attempt 和 error。
- lock metadata 只保存 lock ID、PID、host、operation、target 和时间，不保存环境变量或凭证。
- 根仓另行维护 software field event hash-chain；ADK 不持有业务 prompt 或 operator PII。

## 兼容性与迁移方案
- 3.0 `eval run/report/compare`、export/install/release 命令保持兼容。
- JSON manifest 仍为 SSOT，YAML mirror 保留；新增 release-critical YAML reader allowlist，禁止扩大兼容债务。
- 使用 exact commit 和本地 checksum artifact 进行 3.0.0 -> 3.1.0-rc.1 rehearsal；任何 checksum、install、rollback 或 full gate 失败均不提升 maturity。

## 验证策略
- `rtk bash tests/test_software_m5_ready.sh`
- `rtk bash tests/test_product_maturity_v3.sh`
- `rtk bash tests/run_all.sh --quick`
- `rtk bash tests/run_all.sh --timing-json <evidence>`
- `rtk bash scripts/devkit.sh eval campaign check ...`
- `rtk bash scripts/devkit.sh release rehearse ...`
