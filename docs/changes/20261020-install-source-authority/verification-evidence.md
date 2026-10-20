# 验证证据

## 来源与环境

基线 commit：`10ea70dc36d01625d968a0da3109c8f46b1f6804`。候选为主任务统一更新到 8.0.34 的真实 Git 工作树，最终提交与远端 CI 由主任务绑定。以下是本地源码验收，不是正式发布、原生 runtime 或 Owner 认证。

环境：Python 3.12.14，项目声明的 quality/test 依赖，官方 rtk 1.0.1。命令通过 `rtk proxy` 执行，PATH 指向隔离 venv，`PYTHONPATH=src`；完整回归、strict 和 release check 设置 `ADK_REQUIRE_SUPPORTED_PYTHON=1` 及显式 venv 解释器。Python 3.8/3.11 尚待真实 PR CI。rtk 真实安装与 Provider runtime 是独立边界；本环境未执行实际工作区的 Provider/Execution Policy 运行门禁，产品模块的单元测试不替代该门禁。

## 已通过的本地验证

| Command（由 rtk proxy 执行） | Exit | 实际结果 |
|---|---:|---|
| `python3 tests/test_install_upgrade.py InstallUpgradeTest` / `bash tests/test_install.sh` | 0 | 7 个新升级恢复验收及原安装脚本通过：不同版本字节/mode/receipt恢复、显式来源、重算摘要攻击、历史到期边界 |
| `python3 tests/test_install_upgrade.py ReleaseUpgradeRehearsalTest` | 0 | 真实临时 Git fixture、两个 release artifact、CLI 正向完整演练及反向版本拒绝；fixture 版本由当前 source version 动态派生 |
| `bash tests/test_release_manifest_contract.sh` | 0 | 22 个 archive、4 个 CI authority、既有发布合同和 1 个新增完整 rehearsal 用例通过 |
| `bash tests/test_contract_hardening.sh` | 0 | 41 个合同、8 个 receipt authority、5 个 YAML 边界用例通过 |
| `bash tests/test_target_contracts.sh` | 0 | 目标合同既有正负向检查通过 |
| `bash tests/test_native_trust.sh` | 0 | 6 个 native trust 回归通过；未执行原生运行时 |
| `bash tests/test_docs_cli_alignment.sh` | 0 | 88 份当前文档与 CLI/help/路径检查通过 |
| `bash tests/test_module_size_budget.sh` | 0 | 模块大小/依赖方向预算通过，最大 import fan-out 为 26，限制 28 |
| `ruff check`（7 个受影响源码文件及新增测试） | 0 | 全部检查通过 |
| `mypy`（7 个受影响源码文件） | 0 | 严格类型检查无问题 |
| CI focused strict mypy（既有范围 + 7 个调用链模块，主任务执行） | 0 | 27 个源码文件联合检查无问题；已纳入原 CI 步骤 |
| `git diff --check` | 0 | 无 diff 空白错误 |
| `bash scripts/devkit.sh validate --strict --summary-json` | 0 | 13 agents、57 skills、8 optional skills、8 profiles、7 workflows，failures 为空，governance 5 项通过 |
| `bash scripts/devkit.sh release check --summary-json` | 0 | 8.0.34 发布合同检查通过，failures 为空，runtime_eval_executed=false |
| `bash tests/run_all.sh --timing-json /workspace/scratch/28c22f668291/repair/adk-full-test-timing.json` | 0 | 完整回归 98/98，失败 0；256138 ms，进程退出码已确认 |

首次测试中的 fixture 返回字段错误、脚本变量错误和静态注解不一致已保留在 negative-results.md；对应最终命令通过后才记录本表。

## 独立代码复核

独立代码审查 agent 对生产 diff 和新增测试完成只读复核，未报告阻塞性问题，未重复执行测试。其复核覆盖来源参数全链传递、历史 expiry 唯一例外、当前/旧库存和 target/tool 绑定、旧备份字节/mode 权威，以及原路径/事务边界。本记录不代替人类 Owner/独立 Reviewer 授权。

## 待完成门禁

本地 full、strict validate 与 release check 均已通过，日志为工作区 `repair/adk-full-test.log`，计时 JSON 为上表路径。生产代码与测试在完整回归期间保持稳定，最后仅补充此验证记录。远端 PR CI 与实际 Python 3.8/3.11 结果尚未产生，不声明其通过；主任务继续完成 TASK-005。旧库存不是新选择子集时仍须先恢复原安装；旧 schema/渲染语义不兼容仍 fail closed。
