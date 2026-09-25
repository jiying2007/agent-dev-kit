# 重复试验审查检查点

准备提交 `7482ff6097c7b401800723ca9d1c5d749689faa2` 已应用摘要绑定的本地被测补丁，使用版本同步工具生成7.1.0身份。临时工作流与传输文件已移除，不属于最终资产。

已在本地和远端准备阶段执行32项 trial 回归以及原 comparator、contract registry、packaged schema、module boundary 检查。发布前仍要求本 PR 最终 head 的完整 Python3.11/3.12 回归、平台、安全与打包验证；合并后独立验证 main CI、immutable Release、Root promotion。

## 保留的边界

- 单次 comparator 与 Run Evidence 继续是逐 trial 验证权威，不复制receipt或指标语义。
- task才是统计独立单位；计划应预先冻结，不因某次失败改 task ID、删 trial 或追加到出现有利结果为止。
- 运行时、prompt、bundle 等实际摘要字段与计划比较；环境、provider、参数等引用是调用方测试声明，不是已认证的原生环境证明。
- 需要真实 immutable model revision；别名或中转无法确认revision时标记 alias-unverified并得到inconclusive。
- 统计区间受样本代表性、退化样本和候选选择影响；小型fixtures仅验证实现分支，不证明真实任务收益。
- 所有输出test-only，release_authorized=false，无生命周期或产品资格权限。

准备阶段第一次中止是手写 CHANGELOG diff 的行数标头不匹配；内容摘要校验通过但git apply拒绝，未写入分支实现。校正补丁解析计数后再执行。未降低源码测试或签名/权限门禁。
