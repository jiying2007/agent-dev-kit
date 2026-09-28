# 设计与边界

`scripts/devkit.sh` 已显式设置 `PYTHONPATH` 并选 Python 3；独立的 `tests/run_all.sh` 原先缺少等价的源码定位，多个测试因此在未安装包的机器上报 `ModuleNotFoundError`。另有少数测试调用系统 `python`，在本机被解析为 Python 2，出现语法错误。修复只涉及测试 runner 与测试脚本入口，不改 ADK 包依赖、业务实现或 release 资格。

当前验证：系统 `python3` 为 3.8.10；修复后 `tests/run_all.sh` 汇总为 94 项、93 通过、1 失败。唯一失败 `test_runtime_bundle` 的 3 个内部功能测试通过，但身份命令要求 clean Git commit；本批有未提交工作树改动，需在统一提交后重跑该项。不能把 93/94 写成完整通过，也不能绕过身份门禁。
