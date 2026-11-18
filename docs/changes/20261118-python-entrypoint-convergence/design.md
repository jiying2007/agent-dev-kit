# 最小重构

- 将现有 `devkit.sh` 的解释器解析、版本检查原逻辑移至 `scripts/lib-python-runtime.sh`，`devkit.sh` 只 source 后 exec CLI。
- `version-manager.sh` 的 Python 子命令在解析参数后调用同一选择器；`--help` 和无 Python 的 `unlock` 不增加依赖。
- 使用命令替换获取版本探测结果并校验退出码，消除 process substitution 吞掉进程错误的可能。
- 不新增 Python 包、适配层、工作流、兼容别名或外部状态存储；保留可直接运行的脚本入口，按版本身份原约束晋级。
