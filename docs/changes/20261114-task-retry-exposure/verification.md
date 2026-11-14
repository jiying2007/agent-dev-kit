# 验证记录

源码快照为 `948f49b2ca3ecc56c9632946b67736b0c0047a14`，基线为 `4f77f795ecfba3e6bb1e167eb27cb84cca796845`。27份变更已逐字节核对远端Git对象、本地工作区与上传前摘要，映射和完整差异见 `evidence/source-bindings.json` 与 `evidence/original.patch`。后续本记录和审查回执不改变该源码身份。

## 实际结果

- 新增7项方法回归和2项原有控制：原实现RED出现13个子案例error与1个failure；同一命令GREEN为9/9。全部是synthetic-fixture，不是模型任务。
- `test_run_evidence.sh`：5+27+17=49项通过；`test_effect_trials.sh`：35项通过。实现者原始日志无损复制，保留命令、真实时间和返回码。
- `tests/run_all.sh`：2026-11-14T14:32:24.578535+00:00开始，2026-11-14T14:37:06.467252+00:00结束，102/102入口通过，exit 0，stderr为空。完整日志与各入口计时见 `evidence/full.json` 和 `evidence/full-timing.json`。
- strict validate、module-size/fan-out、完整 `ruff check src tools tests/fixtures/fake_target_runtime.py` 通过；promotion evidence脚本首次因本地包未安装而无法导入，显式PYTHONPATH=src后原命令通过，负结果保留。
- 协调者已用Python 3.12、锁定mypy 2.4.1、真实CI的全部18个路径参数、新缓存及MYPYPATH=src执行完整strict类型检查，输出32个source files无错误。为补齐最终审查的原始记录，再次按同一源码与实际CI参数执行并保存 `evidence/full-type-analysis.json`，真实完成时间为2026-11-14T14:40:18.184268+00:00；前次未落盘结果不伪造成日志。最终受保护CI将再次对实际PR HEAD独立验证。
- 临时Git index纳入全部27份源码变更后的diff格式检查通过；未把untracked文件排除在该检查之外。

## 独立审查与剩余门禁

独立只读审查者此前对四份核心实现/回归/runbook文件以及版本、历史预注册、先导合同分别给出Spec/Quality pass，open blocker/major为0。审查还实际证伪了单次输出兼容、交错guardrail索引、未选证据hardlink覆盖及缓存路径第二次摘要冲突。最终源码与本次事实记录绑定另见typed review-evidence。

PR的八项受保护检查、合并后主线CI、不可变Release和消费者source-only晋级尚不由这份本地验证授予。先导试验及原方案T6单独报告；确定性回归与工程发布不构成真实任务效果、Token/费用或泛化收益证据。
