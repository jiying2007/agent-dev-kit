# Python 3.8 整批测试入口

## 目标

在无预先安装 ADK 包、系统 `python` 可能为 Python 2 的开发机上，`tests/run_all.sh` 仍使用工作树源码与 `python3` 执行整批测试。该入口是 Python 3.8 开发验证，不授予干净提交或正式发布身份。

## 验收

1. runner 从自身路径确定源码根，并将 `src` 加到子测试的 `PYTHONPATH`，保留调用方既有路径。
2. 直接调用 `python` 的测试脚本改用 `python3`，不改变测试断言。
3. Python 3.8 整批回归报告实际 pass/fail；干净提交身份门禁仍须在 clean commit 后单独复核。
