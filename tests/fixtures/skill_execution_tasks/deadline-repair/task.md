# 单个边界错误的修复

已授权仅修复 `retry_policy.py` 的 deadline 边界：已经到达 timeout 的请求不得重试。保持其他字节与原回归用例不变。先用已有 `deadline_cases.py` 的原症状定位；仅改变这一项假设，修复后复测原症状及已经通过的正常路径。若宿主允许执行，可在 work 中运行 `python3 -B -m unittest deadline_cases -v`（不生成额外的字节码缓存）；没有执行渠道就明确保留 not-run。

输出修改后的 `retry_policy.py`，以及 `expected-results.json`：字段 `signal="deadline-boundary"`、`scope="expected-results-only"`，`cases` 依序列出 elapsed_ms 为 0、99、100、101、timeout_ms 均为 100 的 retry_allowed 布尔结果。它是可核对的预期值，不是执行回执。不得修改测试或用输出声明冒充真正的 RED/GREEN。
