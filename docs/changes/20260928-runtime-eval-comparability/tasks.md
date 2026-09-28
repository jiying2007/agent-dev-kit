# 本地任务

- [x] 核对 `run_runtime` 与 `compare_runtime_reports`：现状只比较 ID 顺序，报告缺任务/逐例 prompt 与 grader 身份。
- [x] 增加 runtime 报告的任务集、逐例 prompt、grader、manifest、请求模型和运行时版本字段；模拟模型调用定向验证。
- [x] 比较器拒绝不可比报告并披露逐例改善/退化；执行前冻结任务快照，修改原对象的负例通过。Python 3.8 确定性正负例 7/7 通过。
- [x] 旧历史报告通过 CLI 比较时因缺任务摘要而明确拒绝；伪造布尔指标/quality gate 负例拒绝。
- [x] Python 3.8 完整回归在逐例模型身份核验补丁前为 95 项中 94 项通过；唯一失败 `test_runtime_bundle` 要求 clean commit，内部 3 项通过。补丁后定向比较 7/7 与 Software M5 测试通过，当前快照完整回归待统一收口复跑。
- [x] 将同任务集/grader/模型口径和逐例退化写入既有 `adk-test-strategy`；七个 profile 入口与潜在完整源码各增加 262 字节，体积棘轮 5/5 通过。
- [x] 当前 Python 3.8 quick 回归 52 项中 51 项通过，唯一失败是未提交工作树的 clean commit 身份；逐例模型身份与效应数据快照改动均在本次 quick 内通过。
- [ ] 定向、严格校验、格式和当前快照整批复验；保持本地未提交。
