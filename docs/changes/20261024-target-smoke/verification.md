# F2 实现与定向验证

## 实现

基线 `415590db44e88979185efb850e2339a3f95411ef`，工作分支 `fix/audit-boundaries-20261024`。`process_execution.py` 是 stdlib-only 的进程生命周期 owner，`targets.py` 与 `native_campaign_execution.py` 保留各自业务结果和错误映射。

- smoke stdout/stderr 共用固定 1 MiB 预算；溢出的 chunk 不进入保留缓冲区，失败码为 `runtime_output_budget_exceeded`。
- deadline 包含直接进程退出和全部输出管道关闭；父进程先退出不解除后代持 pipe 的超时约束。
- 失败时 POSIX 发送 SIGKILL 到创建时隔离的原进程组，关闭所有 transport，并等待进程及管道关闭；额外清理等待最多 5 秒。本地探针确认直接子进程已被 reap。该边界不承诺清理主动创建新 session 逃出原进程组的程序。
- 非 POSIX 保留直接子进程终止能力；本轮没有验证 Windows，也不声称等价的后代树清理。
- stdin 采用 Native 现有的 DEVNULL 非交互约定。Native 原有 `native_campaign_output_budget_exceeded` 业务错误、stage evidence 与认证合同未变。
- smoke 结果保持 `caller-supplied-smoke`；结果中只有运行退出码、字节计数与 SHA-256 摘要，不持久化命令/输出正文。共享 owner 的暂存原始字节只供 Native 语义匹配，大小受同一预算限制。

## 实际验证

环境：Linux，Python 3.12.14。Shell 经工作区 `rtk proxy`，Python 来自隔离 `audit-venv`。源码指纹保存在 `evidence/source-fingerprints.json`；这些是本地未提交修复的证据，不是正式发布或认证运行证据。

| 检查 | 实际结果 | 原始输出 |
| --- | --- | --- |
| 修复前 smoke 行为 | 8 项，3 pass / 5 fail，exit 1 | `evidence/red-target-smoke.txt` |
| 第一版提取后的 resource 清理缺口 | 8 项断言虽通过，但有 ResourceWarning，未计为干净成功 | `evidence/first-pass-with-resource-warnings.txt` |
| transport 资源泄漏回归先红 | 1 项 fail，exit 1 | `evidence/red-transport-cleanup.txt` |
| `bash tests/test_target_contracts.sh` | exit 0，原有合同检查及新增 9 项通过，9.051 秒 | `evidence/green-target-contracts.txt` |
| `bash tests/test_native_campaign.sh` | exit 0，34 项通过，7.872 秒，无资源警告 | `evidence/green-native-campaign.txt` |
| `python3 -m unittest discover -s tests -p test_native_campaign_boundaries.py -v` | exit 0，3 项通过 | `evidence/green-native-boundaries.txt` |
| `bash tests/test_module_size_budget.sh` | exit 0，fan-out 26/28，oversize/support debt 均 0 | `evidence/green-module-budget.txt` |
| `git diff --check` | exit 0 | 工具执行结果 |

新增 9 项行为测试覆盖成功、非零退出、stdout/stderr 各 16 MiB、合计超限、合计恰好预算、公共 CLI 非零与摘要脱敏、父进程存活/提前退出的后代 deadline、退出后的 pipe transport 资源关闭。后代探针忽略 SIGTERM，超时返回后直接父进程 PID 已消失，继续等待后临时 marker 仍未产生。管道资源测试在独立 Python 进程开启 ResourceWarning 并触发 GC，要求 stderr 为空。

## 集成阶段待完成

初始定向验证阶段，隔离环境尚未提供 ruff/mypy，未将它们计为通过。后续主 Agent 已安装项目声明的质量工具；下节记录新增的实际质量检查。完整回归及版本/文档一致性检查仍由主 Agent 统一运行，避免与其他变更同时修改测试 fixture。独立 Spec/Quality 复审也由主 Agent 调度；`tasks.md` 的完整回归和复审项保持未完成。

回滚为上一正式版本；本子任务未提交、推送、合并、发布或修改资格状态。

## Focused quality 补充

主 Agent 将新 process owner 纳入 CI focused 选项后发现两项 SIM105。实现者仅将原 `ProcessLookupError` 和 `asyncio.TimeoutError` 的 `try/except/pass` 改为 `contextlib.suppress`；清理动作、等待时长、保留原始异常的语义都不变。没有追加其他 F2 逻辑修改。

- `python3 -m ruff check src/agent_dev_kit/process_execution.py --select E4,E7,E9,F,B,UP,SIM,I`：exit 0，All checks passed。
- `python3 -m mypy --config-file pyproject.toml --cache-dir /tmp/adk-f2-focused-mypy src/agent_dev_kit/process_execution.py`：exit 0，1 source file 通过。
- `PYTHONPATH=src python3 -m unittest discover -s tests -p test_target_smoke.py -v`：exit 0，9/9，通过耗时 9.056 秒，无资源警告。
- `git diff --check`：exit 0。

原始输出见 `evidence/green-suppress-quality.txt`、`evidence/green-suppress-smoke.txt`。原指纹文件保留为此前运行的历史快照，不覆盖旧证据；本次 `process_execution.py` SHA-256 为 `01e3da0bc9cee08055dafafb178c270f8e6ece2a18de2ad542027a1b252d5b9d`。已请独立 reviewer `/root/root_code_audit` 对这两处等价修正复核并更新最终源码绑定。

## Python 3.8 的真实运行补验

采用独立 reviewer 已准备的 CPython 3.8.20 环境，PyYAML 6.0.3、jsonschema 4.17.3。默认隔离执行曾触发超时清理延迟；同源码、同测试、同解释器改用标准 host 执行后，原 live-parent timeout 测试 PASS（3.416 秒，含 2.3 秒 marker 等待），全部 9 项 smoke PASS（9.644 秒），无资源警告。源码和断言未作兼容性补丁；环境关联的负例、对照和归因边界见 `negative-results.md`。最终独立审核仍负责绑定同一源码指纹并复验最低支持版本。
