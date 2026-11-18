# 最小重构

- local-ci parity 先处理 dry-run，真实执行时检查 Docker 后选 CPython 3.12。
- auto-ops 仅 cleanup/optimize 分支选择 CPython 3.12。
- Python 探测同时验证 sys.implementation.name；不覆盖独立标准库救援路径。
- 利用原 test_local_ci_parity、test_performance_ops、test_python_launcher 负例回归；不新增框架或计划任务。
