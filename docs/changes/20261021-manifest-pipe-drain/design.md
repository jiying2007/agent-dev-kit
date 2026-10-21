# 设计

`manifest_query.py` 逐项输出；`grep -q` 命中后可以关闭输入，真实 producer 后续写入触发 `BrokenPipeError`。`set -o pipefail` 正确保留这个非零状态，导致存在性谓词误报。Root 外层读取普通文件的 grep 没有该流式边界。

最小修复是让十一处生产 consumer 使用 `grep -Fx -- "$name" >/dev/null`，读到 EOF 后再返回；测试中同类 nonempty consumer 也完整读取。独立审核发现 `check-runtime-boundary.sh` 的 handoff `must_not` 列表属于同一边界，且 schema 没有 maxItems 上界，已纳入修复；大 guard 清单与移除真实 guard 的负例加入既有 runtime boundary 测试，不放宽扫描排除项。保留 pipefail 和 Python 的 OSError 错误处理，不引入重试、全局 SIGPIPE、吞错或新的查询 API。

确定性回归使用临时目录内的真实查询模块、shell 实现和合同原件，扩充未被引用的名称尾部。它仅验证查询协议和引用检查，不冒充完整资产清单的 schema/语义资格。大尾部远超系统管道容量，不依赖 sleep 或随机重试；子进程均有超时。受控失败 producer 在输出命中行后返回 23，证明修复仍传播上游错误。

该修复增加了命中后的读取工作，复杂度仍为 O(n)，内存保持流式有界。对当前较小的清单影响有限，对大清单则消除了成功路径的提前断流。所有发布身份投影按现有 versioning authority 同步。回滚使用上一不可变版本 8.0.36 的正常升级/回滚链。
