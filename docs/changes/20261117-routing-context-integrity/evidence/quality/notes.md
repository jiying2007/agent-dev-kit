# 实际质量门禁观察

执行者：`ai/root/audit_core`。所有质量命令均经真实 RTK 1.2.0 的 `proxy` 执行，
绝对路径 `/workspace/scratch/fe8de3b42084/verification-tools/rtk`。没有仿造 wrapper。

启动时仅把本轮 `.venv/bin` 加入 PATH，因此 `command -v rtk` 无结果、尝试的
`rtk --version/proxy` 报 command not found。协调者提供既有绝对路径后正常执行；
这一阶段没有运行质量门禁，也没有修改源码。没有把初始失败记为通过。

检查前已阅读 `scripts/check-format.sh`：它只扫描、检查 Git diff 和权限，写入
`/tmp/adk_*_check.txt` 诊断文件，不修改产品源码。因此允许执行原脚本。

## 五项门禁

精确命令、退出码、UTC 起止时间和原始日志 SHA256 分别记录于同名 `.json`。
第一轮为 2026-11-17 12:10:26–12:10:46 UTC，五项实际 exit 0：

- `ruff check src tools tests/fixtures/fake_target_runtime.py`
- `mypy src/agent_dev_kit/contracts src/agent_dev_kit/evidence src/agent_dev_kit/target_adapters src/agent_dev_kit/distribution src/agent_dev_kit/execution_policy src/agent_dev_kit/versioning.py`
- `shellcheck -S error -x -P scripts scripts/*.sh tests/*.sh`
- `pip-audit --strict --progress-spinner off .`：No known vulnerabilities found。
- `bash scripts/check-format.sh`

版本日志：Python 3.12.14、Ruff 0.17.4、mypy 2.4.1、ShellCheck 0.10.0、
pip-audit 2.10.1、Git 2.52.0、bash 5.2.37、RTK 1.2.0。

## Provider 回归归属修正

协调者初次 strict 发现 generic materializer 测试新增 provider 名称，违反既有
runtime-boundary。没有把该输入换成 campaign 不支持的 opencode，也没有扩展
scanner 例外、拆字符串、改变生产 runtime 或删除验证能力。

经协调者同意，将此 provider-specific 记录校验放入既有
`tests/test_runtime_comparison_contract.py`。该模块本来承担 provider 对照/错误
边界并由现有 scanner 明确识别；使用同文件既有 `report()` 和生产
`_attempt_from_report` 构造合法类型的 synthetic 记录，只调用 `_validate_result`，
不执行模型或 runtime。generic materializer 文件不再持有该专属 case。

12:12:26–12:12:30 UTC，`provider-placement-*` 记录实际验证：

- materializer + runtime comparison 两模块共 25 tests PASS；
- `validate --strict` PASS；
- `check-format` PASS；
- 两个修改测试文件的 Ruff PASS。

这些记录仅绑定当时源码。协调者报告 routing 的 IR-2/IR-3 仍在收敛，最终冻结后
应对实际受影响范围作 fresh 验证；第一轮通过不被改称后续修改的最终验证。
